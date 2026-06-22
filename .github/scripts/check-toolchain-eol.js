#!/usr/bin/env node

/**
 * Inventory checked-in Node.js release-line selectors and compare monitored
 * selectors with the official Node.js release schedule.
 */

const fs = require('fs');
const path = require('path');
const { globSync } = require('glob');
const semver = require('semver');
const yaml = require('yaml');

const DEFAULT_NODE_SCHEDULE_URL =
    'https://raw.githubusercontent.com/nodejs/Release/main/schedule.json';
const DEFAULT_WARNING_WINDOW_DAYS = 180;
const MILLIS_PER_DAY = 24 * 60 * 60 * 1000;
const DEFAULT_FETCH_TIMEOUT_MS = 15000;

function toPosixPath(filePath) {
    return filePath.split(path.sep).join('/');
}

function repoRelativePath(repoRoot, absolutePath) {
    return toPosixPath(path.relative(repoRoot, absolutePath));
}

function assertPathWithinRepo(repoRoot, candidatePath) {
    const rootResolved = path.resolve(repoRoot);
    const candidateResolved = path.resolve(candidatePath);
    const relative = path.relative(rootResolved, candidateResolved);
    if (relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))) {
        return candidateResolved;
    }
    throw new Error(`path escapes repository root: ${candidatePath}`);
}

function resolveRepoPath(repoRoot, relativePath) {
    const normalizedRelativePath = String(relativePath).trim().replace(/^['"]|['"]$/g, '');
    return assertPathWithinRepo(repoRoot, path.resolve(repoRoot, normalizedRelativePath));
}

function readJsonFile(filePath) {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function readYamlFile(filePath) {
    const text = fs.readFileSync(filePath, 'utf8');
    const documents = yaml.parseAllDocuments(text);
    for (const document of documents) {
        if (document.errors.length > 0) {
            throw new Error(
                `${filePath}: ${document.errors.map((error) => error.message).join('; ')}`,
            );
        }
    }
    return documents.filter((document) => document.contents !== null).map((document) => document.toJSON());
}

function asArray(value) {
    if (value === undefined || value === null) {
        return [];
    }
    return Array.isArray(value) ? value : [value];
}

function uniqueValues(values) {
    const seen = new Set();
    const result = [];
    for (const value of values) {
        if (value === undefined || value === null) {
            continue;
        }
        const stringValue = String(value).trim();
        if (!stringValue || seen.has(stringValue)) {
            continue;
        }
        seen.add(stringValue);
        result.push(stringValue);
    }
    return result;
}

function addSelector(selectors, selector) {
    selectors.push({
        toolchain: 'node',
        selectorClass: selector.selectorClass,
        sourceType: selector.sourceType,
        origin: selector.origin,
        path: toPosixPath(selector.path),
        rawValue: String(selector.rawValue).trim(),
        referencedPath: selector.referencedPath ? toPosixPath(selector.referencedPath) : undefined,
    });
}

function collectPackageSelectors(repoRoot, selectors, problems) {
    const packageJsonPath = path.join(repoRoot, 'package.json');
    const packageLockPath = path.join(repoRoot, 'package-lock.json');
    let packageJsonEngine;
    let packageLockEngine;

    if (fs.existsSync(packageJsonPath)) {
        const packageJson = readJsonFile(packageJsonPath);
        packageJsonEngine = packageJson.engines && packageJson.engines.node;
        if (typeof packageJsonEngine === 'string' && packageJsonEngine.trim()) {
            addSelector(selectors, {
                selectorClass: 'support-floor',
                sourceType: 'package-json:engines.node',
                origin: 'root package engines.node',
                path: 'package.json',
                rawValue: packageJsonEngine,
            });
        }
    }

    if (fs.existsSync(packageLockPath)) {
        const packageLock = readJsonFile(packageLockPath);
        packageLockEngine =
            packageLock.packages &&
            packageLock.packages[''] &&
            packageLock.packages[''].engines &&
            packageLock.packages[''].engines.node;
        if (typeof packageLockEngine === 'string' && packageLockEngine.trim()) {
            addSelector(selectors, {
                selectorClass: 'support-floor',
                sourceType: 'package-lock:root.engines.node',
                origin: 'root package-lock mirror',
                path: 'package-lock.json',
                rawValue: packageLockEngine,
            });
        }
    }

    if (
        typeof packageJsonEngine === 'string' &&
        typeof packageLockEngine === 'string' &&
        packageJsonEngine.trim() !== packageLockEngine.trim()
    ) {
        problems.push({
            path: 'package-lock.json',
            message:
                `package-lock root engines.node (${packageLockEngine}) does not match ` +
                `package.json engines.node (${packageJsonEngine}).`,
        });
    }
}

function getWorkflowFiles(repoRoot) {
    return globSync('.github/workflows/**/*.{yml,yaml}', {
        cwd: repoRoot,
        nodir: true,
        dot: true,
        windowsPathsNoEscape: true,
    }).sort();
}

function getAzurePipelineFiles(repoRoot) {
    const patterns = [
        'azure-pipelines.yml',
        'azure-pipelines.yaml',
        '.azuredevops/pipelines/**/*.{yml,yaml}',
    ];
    const files = new Set();
    for (const pattern of patterns) {
        for (const filePath of globSync(pattern, {
            cwd: repoRoot,
            nodir: true,
            dot: true,
            windowsPathsNoEscape: true,
        })) {
            files.add(filePath);
        }
    }
    return [...files].sort();
}

function isSetupNodeStep(step) {
    return (
        step &&
        typeof step === 'object' &&
        typeof step.uses === 'string' &&
        /^actions\/setup-node@/i.test(step.uses.trim())
    );
}

function collectGithubMatrixValues(matrix, key) {
    if (!matrix || typeof matrix !== 'object') {
        return [];
    }

    const values = [];
    if (Object.prototype.hasOwnProperty.call(matrix, key)) {
        values.push(...asArray(matrix[key]));
    }
    if (Array.isArray(matrix.include)) {
        for (const includeEntry of matrix.include) {
            if (
                includeEntry &&
                typeof includeEntry === 'object' &&
                Object.prototype.hasOwnProperty.call(includeEntry, key)
            ) {
                values.push(includeEntry[key]);
            }
        }
    }
    return uniqueValues(values);
}

function resolveGithubExpression(value, matrix) {
    if (typeof value !== 'string') {
        return uniqueValues([value]).map((rawValue) => ({ rawValue, origin: 'literal' }));
    }

    const matrixMatch = value.match(/^\s*\$\{\{\s*matrix\.([A-Za-z0-9_.-]+)\s*\}\}\s*$/);
    if (matrixMatch) {
        return collectGithubMatrixValues(matrix, matrixMatch[1]).map((rawValue) => ({
            rawValue,
            origin: `matrix.${matrixMatch[1]}`,
        }));
    }

    return [{ rawValue: value, origin: 'literal' }];
}

function readVersionFileSelector(repoRoot, filePathValue, sourcePath, sourceType, problems) {
    let referencedAbsolutePath;
    try {
        referencedAbsolutePath = resolveRepoPath(repoRoot, filePathValue);
    } catch (error) {
        problems.push({ path: sourcePath, message: error.message });
        return [];
    }

    if (!fs.existsSync(referencedAbsolutePath)) {
        problems.push({
            path: sourcePath,
            message: `referenced Node.js version file does not exist: ${filePathValue}`,
        });
        return [];
    }

    const realRepoRoot = fs.realpathSync(repoRoot);
    const realReferencedPath = fs.realpathSync(referencedAbsolutePath);
    assertPathWithinRepo(realRepoRoot, realReferencedPath);

    const referencedPath = repoRelativePath(repoRoot, referencedAbsolutePath);
    const content = fs.readFileSync(referencedAbsolutePath, 'utf8');
    let rawValue;

    if (path.basename(referencedAbsolutePath) === '.tool-versions') {
        const nodeLine = content
            .split(/\r?\n/)
            .map((line) => line.trim())
            .find((line) => line && !line.startsWith('#') && /^nodejs\s+/i.test(line));
        if (nodeLine) {
            rawValue = nodeLine.split(/\s+/)[1];
        }
    } else {
        rawValue = content
            .split(/\r?\n/)
            .map((line) => line.trim())
            .find((line) => line && !line.startsWith('#'));
    }

    if (!rawValue) {
        problems.push({
            path: referencedPath,
            message: `referenced Node.js version file does not contain a selector.`,
        });
        return [];
    }

    return [
        {
            selectorClass: 'ci-runtime',
            sourceType,
            origin: 'version-file',
            path: sourcePath,
            rawValue,
            referencedPath,
        },
    ];
}

function collectGithubWorkflowSelectors(repoRoot, selectors, problems) {
    for (const relativeWorkflowPath of getWorkflowFiles(repoRoot)) {
        const workflowPath = path.join(repoRoot, relativeWorkflowPath);
        for (const workflow of readYamlFile(workflowPath)) {
            if (!workflow || typeof workflow !== 'object' || !workflow.jobs) {
                continue;
            }

            for (const job of Object.values(workflow.jobs)) {
                if (!job || typeof job !== 'object') {
                    continue;
                }
                const matrix = job.strategy && job.strategy.matrix;
                for (const step of asArray(job.steps)) {
                    if (!isSetupNodeStep(step)) {
                        continue;
                    }

                    const stepWith = step.with || {};
                    if (Object.prototype.hasOwnProperty.call(stepWith, 'node-version')) {
                        for (const resolved of resolveGithubExpression(stepWith['node-version'], matrix)) {
                            addSelector(selectors, {
                                selectorClass: 'ci-runtime',
                                sourceType: 'github-actions:setup-node node-version',
                                origin: resolved.origin,
                                path: relativeWorkflowPath,
                                rawValue: resolved.rawValue,
                            });
                        }
                    }

                    if (Object.prototype.hasOwnProperty.call(stepWith, 'node-version-file')) {
                        for (const resolved of resolveGithubExpression(
                            stepWith['node-version-file'],
                            matrix,
                        )) {
                            for (const selector of readVersionFileSelector(
                                repoRoot,
                                resolved.rawValue,
                                relativeWorkflowPath,
                                'github-actions:setup-node node-version-file',
                                problems,
                            )) {
                                addSelector(selectors, selector);
                            }
                        }
                    }
                }
            }
        }
    }
}

function collectParameters(parameters) {
    const result = new Map();
    for (const parameter of asArray(parameters)) {
        if (!parameter || typeof parameter !== 'object' || !parameter.name) {
            continue;
        }
        result.set(String(parameter.name), {
            defaultValue: parameter.default,
            values: asArray(parameter.values),
        });
    }
    return result;
}

function mergeMaps(...maps) {
    const merged = new Map();
    for (const map of maps) {
        for (const [key, value] of map.entries()) {
            merged.set(key, value);
        }
    }
    return merged;
}

function collectVariables(variables) {
    const result = new Map();
    if (!variables) {
        return result;
    }

    if (Array.isArray(variables)) {
        for (const variable of variables) {
            if (variable && typeof variable === 'object' && variable.name && variable.value !== undefined) {
                result.set(String(variable.name), variable.value);
            }
        }
        return result;
    }

    if (typeof variables === 'object') {
        for (const [key, value] of Object.entries(variables)) {
            if (value && typeof value === 'object' && Object.prototype.hasOwnProperty.call(value, 'value')) {
                result.set(key, value.value);
            } else {
                result.set(key, value);
            }
        }
    }
    return result;
}

function collectAzureMatrixValues(strategy, key) {
    if (!strategy || typeof strategy !== 'object' || !strategy.matrix) {
        return [];
    }

    const values = [];
    for (const matrixEntry of Object.values(strategy.matrix)) {
        if (
            matrixEntry &&
            typeof matrixEntry === 'object' &&
            Object.prototype.hasOwnProperty.call(matrixEntry, key)
        ) {
            values.push(matrixEntry[key]);
        }
    }
    return uniqueValues(values);
}

function resolveAzureSelectorValue(value, context, sourcePath, problems) {
    if (typeof value !== 'string') {
        return [{ rawValue: value, origin: 'literal' }];
    }

    const parameterMatch = value.match(
        /^\s*\$\{\{\s*parameters\.([A-Za-z0-9_.-]+)\s*\}\}\s*$/,
    );
    if (parameterMatch) {
        const parameterName = parameterMatch[1];
        const parameter = context.parameters.get(parameterName);
        if (!parameter) {
            problems.push({
                path: sourcePath,
                message:
                    `Azure Pipelines parameter "${parameterName}" referenced by ${value.trim()} is not ` +
                    'declared in this file, so its Node.js selector cannot be verified from checked-in YAML.',
            });
            return [];
        }
        const values = uniqueValues([parameter.defaultValue, ...parameter.values]);
        if (values.length === 0) {
            problems.push({
                path: sourcePath,
                message:
                    `Azure Pipelines parameter "${parameterName}" has no checked-in default or values, ` +
                    'so its Node.js selector cannot be verified from checked-in YAML.',
            });
        }
        return values.map((rawValue) => ({
            rawValue,
            origin:
                parameter.values.length > 0
                    ? `parameters.${parameterName} default-or-values`
                    : `parameters.${parameterName} default`,
        }));
    }

    const macroMatch = value.match(/^\s*\$\(([A-Za-z0-9_.-]+)\)\s*$/);
    if (macroMatch) {
        const variableName = macroMatch[1];
        const values = [];
        if (context.variables.has(variableName)) {
            values.push(context.variables.get(variableName));
        }
        values.push(...collectAzureMatrixValues(context.strategy, variableName));
        const resolvedValues = uniqueValues(values);
        if (resolvedValues.length === 0) {
            problems.push({
                path: sourcePath,
                message:
                    `Azure Pipelines variable "${variableName}" referenced by ${value.trim()} is not defined ` +
                    'by a checked-in variable or matrix, so its Node.js selector cannot be verified from ' +
                    'checked-in YAML (it may be provided only at queue time).',
            });
        }
        return resolvedValues.map((rawValue) => ({
            rawValue,
            origin: `variable-or-matrix.${variableName}`,
        }));
    }

    return [{ rawValue: value, origin: 'literal' }];
}

function isAzureNodeTask(step) {
    if (!step || typeof step !== 'object' || typeof step.task !== 'string') {
        return false;
    }
    return /^(UseNode@1|NodeTool@0)$/i.test(step.task.trim());
}

function collectAzureStepSelectors(repoRoot, relativePipelinePath, steps, context, selectors, problems) {
    for (const step of asArray(steps)) {
        if (!isAzureNodeTask(step)) {
            continue;
        }

        const taskName = step.task.trim();
        const inputs = step.inputs || {};
        if (/^UseNode@1$/i.test(taskName) && Object.prototype.hasOwnProperty.call(inputs, 'version')) {
            for (const resolved of resolveAzureSelectorValue(inputs.version, context, relativePipelinePath, problems)) {
                addSelector(selectors, {
                    selectorClass: 'ci-runtime',
                    sourceType: 'azure-pipelines:UseNode@1 version',
                    origin: resolved.origin,
                    path: relativePipelinePath,
                    rawValue: resolved.rawValue,
                });
            }
        }

        if (/^NodeTool@0$/i.test(taskName)) {
            const versionSource = String(inputs.versionSource || '').trim();
            if (
                /^fromFile$/i.test(versionSource) &&
                Object.prototype.hasOwnProperty.call(inputs, 'versionFilePath')
            ) {
                for (const resolved of resolveAzureSelectorValue(inputs.versionFilePath, context, relativePipelinePath, problems)) {
                    for (const selector of readVersionFileSelector(
                        repoRoot,
                        resolved.rawValue,
                        relativePipelinePath,
                        'azure-pipelines:NodeTool@0 versionFilePath',
                        problems,
                    )) {
                        addSelector(selectors, selector);
                    }
                }
            } else if (Object.prototype.hasOwnProperty.call(inputs, 'versionSpec')) {
                for (const resolved of resolveAzureSelectorValue(inputs.versionSpec, context, relativePipelinePath, problems)) {
                    addSelector(selectors, {
                        selectorClass: 'ci-runtime',
                        sourceType: 'azure-pipelines:NodeTool@0 versionSpec',
                        origin: resolved.origin,
                        path: relativePipelinePath,
                        rawValue: resolved.rawValue,
                    });
                }
            }
        }
    }
}

function collectAzureJobSelectors(repoRoot, relativePipelinePath, job, context, selectors, problems) {
    if (!job || typeof job !== 'object') {
        return;
    }
    const jobContext = {
        parameters: context.parameters,
        variables: mergeMaps(context.variables, collectVariables(job.variables)),
        strategy: job.strategy,
    };
    collectAzureStepSelectors(repoRoot, relativePipelinePath, job.steps, jobContext, selectors, problems);
}

function collectAzurePipelineSelectors(repoRoot, selectors, problems) {
    for (const relativePipelinePath of getAzurePipelineFiles(repoRoot)) {
        const pipelinePath = path.join(repoRoot, relativePipelinePath);
        for (const pipeline of readYamlFile(pipelinePath)) {
            if (!pipeline || typeof pipeline !== 'object') {
                continue;
            }

            const rootContext = {
                parameters: collectParameters(pipeline.parameters),
                variables: collectVariables(pipeline.variables),
                strategy: pipeline.strategy,
            };

            collectAzureStepSelectors(
                repoRoot,
                relativePipelinePath,
                pipeline.steps,
                rootContext,
                selectors,
                problems,
            );

            for (const job of asArray(pipeline.jobs)) {
                collectAzureJobSelectors(
                    repoRoot,
                    relativePipelinePath,
                    job,
                    rootContext,
                    selectors,
                    problems,
                );
            }

            for (const stage of asArray(pipeline.stages)) {
                if (!stage || typeof stage !== 'object') {
                    continue;
                }
                const stageContext = {
                    parameters: rootContext.parameters,
                    variables: mergeMaps(rootContext.variables, collectVariables(stage.variables)),
                    strategy: stage.strategy || rootContext.strategy,
                };
                collectAzureStepSelectors(
                    repoRoot,
                    relativePipelinePath,
                    stage.steps,
                    stageContext,
                    selectors,
                    problems,
                );
                for (const job of asArray(stage.jobs)) {
                    collectAzureJobSelectors(
                        repoRoot,
                        relativePipelinePath,
                        job,
                        stageContext,
                        selectors,
                        problems,
                    );
                }
            }
        }
    }
}

function collectNodeSelectors(repoRoot = process.cwd()) {
    const resolvedRepoRoot = path.resolve(repoRoot);
    const selectors = [];
    const problems = [];

    collectPackageSelectors(resolvedRepoRoot, selectors, problems);
    collectGithubWorkflowSelectors(resolvedRepoRoot, selectors, problems);
    collectAzurePipelineSelectors(resolvedRepoRoot, selectors, problems);

    return { selectors, problems };
}

function selectorReleaseLine(selector) {
    const rawValue = selector.rawValue.replace(/^v(?=\d)/i, '').trim();
    const minimumVersion = semver.minVersion(rawValue);
    if (!minimumVersion) {
        return null;
    }
    return minimumVersion.major;
}

function parseUtcDateOnly(dateText) {
    const match = String(dateText).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) {
        throw new Error(`expected date in YYYY-MM-DD form: ${dateText}`);
    }
    return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
}

function normalizeNodeSchedule(scheduleJson) {
    const releases = new Map();
    for (const [key, value] of Object.entries(scheduleJson)) {
        const match = key.match(/^v?(\d+)(?:\.\d+)?$/);
        if (!match || !value || typeof value !== 'object' || !value.end) {
            continue;
        }
        releases.set(Number(match[1]), {
            releaseLine: Number(match[1]),
            eolDate: String(value.end),
        });
    }
    return releases;
}

function evaluateSelectors(selectors, scheduleJson, options = {}) {
    const asOfDate = parseUtcDateOnly(
        options.asOfDate || new Date().toISOString().slice(0, 10),
    );
    const warningWindowDays = Number(options.warningWindowDays ?? DEFAULT_WARNING_WINDOW_DAYS);
    const schedule = normalizeNodeSchedule(scheduleJson);
    const findings = [];
    const problems = [];

    for (const selector of selectors) {
        if (!['ci-runtime', 'support-floor'].includes(selector.selectorClass)) {
            continue;
        }
        const releaseLine = selectorReleaseLine(selector);
        if (releaseLine === null) {
            problems.push({
                path: selector.path,
                message: `unable to parse Node.js selector "${selector.rawValue}" from ${selector.sourceType}.`,
            });
            continue;
        }

        const scheduleEntry = schedule.get(releaseLine);
        if (!scheduleEntry) {
            problems.push({
                path: selector.path,
                message:
                    `Node.js ${releaseLine} from selector "${selector.rawValue}" is not present ` +
                    'in the Node.js release schedule.',
            });
            continue;
        }

        const eolDate = parseUtcDateOnly(scheduleEntry.eolDate);
        const daysUntilEol = Math.floor((eolDate.getTime() - asOfDate.getTime()) / MILLIS_PER_DAY);
        let status = 'supported';
        if (daysUntilEol <= 0) {
            // The schedule's end date is the EOL date itself, so "at EOL"
            // (daysUntilEol === 0) gets the same stronger signal as "past EOL".
            status = 'eol';
        } else if (daysUntilEol <= warningWindowDays) {
            status = 'near-eol';
        }

        findings.push({
            ...selector,
            releaseLine,
            eolDate: scheduleEntry.eolDate,
            daysUntilEol,
            status,
        });
    }

    return { findings, problems };
}

async function loadSchedule(options) {
    if (options.scheduleFile) {
        return readJsonFile(path.resolve(options.scheduleFile));
    }

    const scheduleUrl = options.scheduleUrl || DEFAULT_NODE_SCHEDULE_URL;
    const timeoutMs = Number(options.fetchTimeoutMs ?? DEFAULT_FETCH_TIMEOUT_MS);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(scheduleUrl, { signal: controller.signal });
        if (!response.ok) {
            throw new Error(`failed to fetch Node.js release schedule from ${scheduleUrl}: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        if (error && error.name === 'AbortError') {
            throw new Error(
                `timed out after ${timeoutMs}ms fetching Node.js release schedule from ${scheduleUrl}.`,
            );
        }
        throw error;
    } finally {
        clearTimeout(timer);
    }
}

function parseArgs(argv) {
    const options = {
        repoRoot: process.cwd(),
        scheduleUrl: DEFAULT_NODE_SCHEDULE_URL,
        warningWindowDays: Number(
            process.env.TOOLCHAIN_EOL_WARNING_DAYS || DEFAULT_WARNING_WINDOW_DAYS,
        ),
        json: false,
    };

    for (let index = 0; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--repo-root') {
            options.repoRoot = argv[++index];
        } else if (arg === '--schedule-file') {
            options.scheduleFile = argv[++index];
        } else if (arg === '--schedule-url') {
            options.scheduleUrl = argv[++index];
        } else if (arg === '--warning-window-days') {
            options.warningWindowDays = Number(argv[++index]);
        } else if (arg === '--as-of') {
            options.asOfDate = argv[++index];
        } else if (arg === '--json') {
            options.json = true;
        } else if (arg === '--help' || arg === '-h') {
            options.help = true;
        } else {
            throw new Error(`unknown argument: ${arg}`);
        }
    }

    if (!Number.isInteger(options.warningWindowDays) || options.warningWindowDays < 0) {
        throw new Error('--warning-window-days must be a non-negative integer.');
    }

    return options;
}

function printHelp() {
    console.log(`Usage: node .github/scripts/check-toolchain-eol.js [options]

Options:
  --repo-root PATH             Repository root to scan. Defaults to cwd.
  --schedule-file PATH         Read Node.js release schedule JSON from a fixture file.
  --schedule-url URL           Fetch Node.js release schedule JSON from URL.
  --warning-window-days DAYS   Warn/fail when EOL is within DAYS. Default: 180.
  --as-of YYYY-MM-DD           Evaluate against this UTC date. Defaults to today.
  --json                       Emit machine-readable JSON.
`);
}

function githubAnnotationLevel(finding) {
    return finding.status === 'supported' ? 'notice' : 'error';
}

function escapeWorkflowData(value) {
    // Percent MUST be escaped first; otherwise a literal "%0A" in the text would
    // be decoded as a newline by the runner command processor (and our own
    // inserted %0D/%0A escapes would be double-encoded).
    return String(value)
        .replace(/%/g, '%25')
        .replace(/\r/g, '%0D')
        .replace(/\n/g, '%0A');
}

function escapeWorkflowProperty(value) {
    return escapeWorkflowData(value)
        .replace(/:/g, '%3A')
        .replace(/,/g, '%2C');
}

function printGithubAnnotation(level, pathName, message) {
    console.log(`::${level} file=${escapeWorkflowProperty(pathName)}::${escapeWorkflowData(message)}`);
}

function renderTextReport(result, options) {
    const monitoredFindings = result.findings.filter((finding) =>
        ['ci-runtime', 'support-floor'].includes(finding.selectorClass),
    );
    const failingFindings = monitoredFindings.filter((finding) => finding.status !== 'supported');

    console.log('Toolchain EOL monitor');
    console.log(`Data source: ${options.scheduleFile || options.scheduleUrl || DEFAULT_NODE_SCHEDULE_URL}`);
    console.log(`Warning window: ${options.warningWindowDays} day(s)`);
    console.log('');

    if (monitoredFindings.length === 0) {
        console.log('No monitored Node.js selectors were discovered.');
    } else {
        console.log('Monitored Node.js selectors:');
        for (const finding of monitoredFindings) {
            const detail = finding.referencedPath ? ` via ${finding.referencedPath}` : '';
            console.log(
                `- ${finding.selectorClass} Node.js ${finding.releaseLine} ` +
                    `(${finding.rawValue}) in ${finding.path}${detail}: ` +
                    `${finding.status}; EOL ${finding.eolDate}; ` +
                    `${finding.daysUntilEol} day(s) remaining`,
            );
        }
    }

    if (result.problems.length > 0) {
        console.log('');
        console.log('Inventory problems:');
        for (const problem of result.problems) {
            console.log(`- ${problem.path}: ${problem.message}`);
            printGithubAnnotation('error', problem.path, problem.message);
        }
    }

    for (const finding of failingFindings) {
        const message =
            finding.status === 'eol'
                ? `Node.js ${finding.releaseLine} is past EOL (${finding.eolDate}).`
                : `Node.js ${finding.releaseLine} reaches EOL on ${finding.eolDate}, ` +
                  `within the ${options.warningWindowDays}-day warning window.`;
        printGithubAnnotation(githubAnnotationLevel(finding), finding.path, message);
    }

    if (result.problems.length === 0 && failingFindings.length === 0) {
        console.log('');
        console.log('All monitored Node.js selectors are outside the configured warning window.');
    }
}

async function runCli(argv = process.argv.slice(2)) {
    const options = parseArgs(argv);
    if (options.help) {
        printHelp();
        return 0;
    }

    const inventory = collectNodeSelectors(options.repoRoot);
    const schedule = await loadSchedule(options);
    const evaluation = evaluateSelectors(inventory.selectors, schedule, options);
    const result = {
        selectors: inventory.selectors,
        findings: evaluation.findings,
        problems: [...inventory.problems, ...evaluation.problems],
    };

    if (options.json) {
        console.log(JSON.stringify(result, null, 2));
    } else {
        renderTextReport(result, options);
    }

    const hasFailingFinding = result.findings.some((finding) => finding.status !== 'supported');
    return result.problems.length > 0 || hasFailingFinding ? 1 : 0;
}

if (require.main === module) {
    runCli()
        .then((exitCode) => {
            process.exit(exitCode);
        })
        .catch((error) => {
            console.error(`Error: ${error.message}`);
            process.exit(1);
        });
}

module.exports = {
    DEFAULT_NODE_SCHEDULE_URL,
    DEFAULT_WARNING_WINDOW_DAYS,
    collectNodeSelectors,
    escapeWorkflowData,
    evaluateSelectors,
    loadSchedule,
    normalizeNodeSchedule,
    parseArgs,
    runCli,
    selectorReleaseLine,
};
