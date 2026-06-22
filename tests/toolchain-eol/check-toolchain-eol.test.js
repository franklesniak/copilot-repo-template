const assert = require('assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { test, after } = require('node:test');

const scanner = require('../../.github/scripts/check-toolchain-eol.js');

const FIXTURE_SCHEDULE = require('./fixtures/node-schedule.json');

const createdTempRepos = [];

function makeTempRepo() {
    const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'toolchain-eol-'));
    createdTempRepos.push(repoRoot);
    return repoRoot;
}

after(() => {
    for (const repoRoot of createdTempRepos) {
        fs.rmSync(repoRoot, { recursive: true, force: true });
    }
});

function writeFile(repoRoot, relativePath, content) {
    const filePath = path.join(repoRoot, relativePath);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf8');
}

function selectorKey(selector) {
    const referenced = selector.referencedPath ? ` via ${selector.referencedPath}` : '';
    return `${selector.selectorClass}|${selector.sourceType}|${selector.origin}|${selector.rawValue}|${selector.path}${referenced}`;
}

test('discovers and classifies checked-in Node.js selectors without action-version false positives', () => {
    const repoRoot = makeTempRepo();
    writeFile(
        repoRoot,
        'package.json',
        JSON.stringify({ engines: { node: '>=22.0.0' } }, null, 2),
    );
    writeFile(
        repoRoot,
        'package-lock.json',
        JSON.stringify(
            {
                packages: {
                    '': { engines: { node: '>=22.0.0' } },
                    'node_modules/transitive': { engines: { node: '>=10' } },
                },
            },
            null,
            2,
        ),
    );
    writeFile(repoRoot, '.nvmrc', '23\n');
    writeFile(repoRoot, '.node-version', '24\n');

    writeFile(
        repoRoot,
        '.github/workflows/literal.yml',
        `
name: Literal
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v6
        with:
          node-version: "24"
`,
    );
    writeFile(
        repoRoot,
        '.github/workflows/matrix.yml',
        `
name: Matrix
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ["22", "24"]
    steps:
      - uses: actions/setup-node@v6
        with:
          node-version: \${{ matrix.node-version }}
`,
    );
    writeFile(
        repoRoot,
        '.github/workflows/version-file.yml',
        `
name: Version file
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v6
        with:
          node-version-file: ".nvmrc"
`,
    );

    writeFile(
        repoRoot,
        '.azuredevops/pipelines/parameters.yml',
        `
parameters:
  - name: nodeVersion
    type: string
    default: "22"
    values:
      - "22"
      - "24"
steps:
  - task: UseNode@1
    inputs:
      version: \${{ parameters.nodeVersion }}
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/variables.yml',
        `
variables:
  nodeVersion: "22"
steps:
  - task: UseNode@1
    inputs:
      version: "$(nodeVersion)"
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/stage-and-job-variables.yml',
        `
stages:
  - stage: build
    variables:
      stageNodeVersion: "22"
    jobs:
      - job: stageVariable
        steps:
          - task: UseNode@1
            inputs:
              version: "$(stageNodeVersion)"
      - job: jobVariable
        variables:
          jobNodeVersion: "24"
        steps:
          - task: UseNode@1
            inputs:
              version: "$(jobNodeVersion)"
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/matrix.yml',
        `
jobs:
  - job: test
    strategy:
      matrix:
        node22:
          nodeVersion: "22"
        node24:
          nodeVersion: "24"
    steps:
      - task: UseNode@1
        inputs:
          version: "$(nodeVersion)"
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/nodetool.yml',
        `
steps:
  - task: NodeTool@0
    inputs:
      versionSpec: "23"
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/from-file.yml',
        `
steps:
  - task: NodeTool@0
    inputs:
      versionSource: "fromFile"
      versionFilePath: ".node-version"
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/use-node.yml',
        `
steps:
  - task: UseNode@1
    inputs:
      version: "24"
`,
    );

    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);

    const keys = inventory.selectors.map(selectorKey);
    assert(keys.includes('support-floor|package-json:engines.node|root package engines.node|>=22.0.0|package.json'));
    assert(keys.includes('support-floor|package-lock:root.engines.node|root package-lock mirror|>=22.0.0|package-lock.json'));
    assert(keys.includes('ci-runtime|github-actions:setup-node node-version|literal|24|.github/workflows/literal.yml'));
    assert(keys.includes('ci-runtime|github-actions:setup-node node-version|matrix.node-version|22|.github/workflows/matrix.yml'));
    assert(keys.includes('ci-runtime|github-actions:setup-node node-version|matrix.node-version|24|.github/workflows/matrix.yml'));
    assert(keys.includes('ci-runtime|github-actions:setup-node node-version-file|version-file|23|.github/workflows/version-file.yml via .nvmrc'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|parameters.nodeVersion default-or-values|22|.azuredevops/pipelines/parameters.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|parameters.nodeVersion default-or-values|24|.azuredevops/pipelines/parameters.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|variable-or-matrix.nodeVersion|22|.azuredevops/pipelines/variables.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|variable-or-matrix.stageNodeVersion|22|.azuredevops/pipelines/stage-and-job-variables.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|variable-or-matrix.jobNodeVersion|24|.azuredevops/pipelines/stage-and-job-variables.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|variable-or-matrix.nodeVersion|24|.azuredevops/pipelines/matrix.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:NodeTool@0 versionSpec|literal|23|.azuredevops/pipelines/nodetool.yml'));
    assert(keys.includes('ci-runtime|azure-pipelines:NodeTool@0 versionFilePath|version-file|24|.azuredevops/pipelines/from-file.yml via .node-version'));
    assert(keys.includes('ci-runtime|azure-pipelines:UseNode@1 version|literal|24|.azuredevops/pipelines/use-node.yml'));
    assert(!keys.some((key) => key.includes('setup-node@v6')));
    assert(!keys.some((key) => key.includes('>=10')));
});

test('evaluates support-floor ranges and EOL warning-window status', () => {
    const selectors = [
        {
            toolchain: 'node',
            selectorClass: 'support-floor',
            sourceType: 'package-json:engines.node',
            origin: 'root package engines.node',
            path: 'package.json',
            rawValue: '>=22.0.0',
        },
        {
            toolchain: 'node',
            selectorClass: 'ci-runtime',
            sourceType: 'github-actions:setup-node node-version',
            origin: 'literal',
            path: '.github/workflows/eol.yml',
            rawValue: '23',
        },
        {
            toolchain: 'node',
            selectorClass: 'ci-runtime',
            sourceType: 'github-actions:setup-node node-version',
            origin: 'literal',
            path: '.github/workflows/supported.yml',
            rawValue: '24',
        },
    ];

    const result = scanner.evaluateSelectors(selectors, FIXTURE_SCHEDULE, {
        asOfDate: '2026-01-15',
        warningWindowDays: 180,
    });

    assert.deepEqual(result.problems, []);

    const statusByPath = new Map(result.findings.map((finding) => [finding.path, finding]));
    assert.equal(statusByPath.get('package.json').releaseLine, 22);
    assert.equal(statusByPath.get('package.json').status, 'near-eol');
    assert.equal(statusByPath.get('.github/workflows/eol.yml').status, 'eol');
    assert.equal(statusByPath.get('.github/workflows/supported.yml').status, 'supported');
});

test('reports package-lock root engine drift without reading transitive engines as policy', () => {
    const repoRoot = makeTempRepo();
    writeFile(
        repoRoot,
        'package.json',
        JSON.stringify({ engines: { node: '>=22.0.0' } }, null, 2),
    );
    writeFile(
        repoRoot,
        'package-lock.json',
        JSON.stringify(
            {
                packages: {
                    '': { engines: { node: '>=24.0.0' } },
                    'node_modules/transitive': { engines: { node: '>=8' } },
                },
            },
            null,
            2,
        ),
    );

    const inventory = scanner.collectNodeSelectors(repoRoot);

    assert.equal(inventory.problems.length, 1);
    assert.match(inventory.problems[0].message, /does not match/);
    assert.equal(
        inventory.selectors.filter((selector) => selector.sourceType === 'package-lock:root.engines.node')
            .length,
        1,
    );
    assert(!inventory.selectors.some((selector) => selector.rawValue === '>=8'));
});

test('handles unquoted numeric GitHub Actions node-version selectors', () => {
    const repoRoot = makeTempRepo();
    writeFile(
        repoRoot,
        '.github/workflows/numeric.yml',
        `
name: Numeric
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-node@v6
        with:
          node-version: 24
`,
    );

    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);

    const keys = inventory.selectors.map(selectorKey);
    assert(keys.includes('ci-runtime|github-actions:setup-node node-version|literal|24|.github/workflows/numeric.yml'));
    assert(!inventory.selectors.some((selector) => selector.rawValue === 'undefined'));

    // A non-string selector must still evaluate cleanly rather than cascading
    // into a false "unable to parse" inventory problem.
    const evaluation = scanner.evaluateSelectors(inventory.selectors, FIXTURE_SCHEDULE, {
        asOfDate: '2026-01-15',
        warningWindowDays: 180,
    });
    assert.deepEqual(evaluation.problems, []);
    assert.equal(evaluation.findings[0].releaseLine, 24);
});

test('escapes percent before CR/LF in GitHub Actions annotation data', () => {
    // A literal "%0A" in the text must not be decodable as a newline by the
    // runner command processor: the percent is escaped first, yielding "%250A".
    assert.equal(scanner.escapeWorkflowData('before%0Aafter'), 'before%250Aafter');
    // Real control characters are still encoded.
    assert.equal(scanner.escapeWorkflowData('a\r\nb'), 'a%0D%0Ab');
    // A bare percent is encoded.
    assert.equal(scanner.escapeWorkflowData('100%'), '100%25');
});

test('classifies a selector evaluated on its EOL date as eol', () => {
    const selectors = [
        {
            toolchain: 'node',
            selectorClass: 'ci-runtime',
            sourceType: 'github-actions:setup-node node-version',
            origin: 'literal',
            path: '.github/workflows/on-eol-date.yml',
            rawValue: '22',
        },
    ];

    // FIXTURE_SCHEDULE v22 end is 2026-07-01; evaluating on that exact date
    // means daysUntilEol === 0, which must be the stronger "eol" signal.
    const result = scanner.evaluateSelectors(selectors, FIXTURE_SCHEDULE, {
        asOfDate: '2026-07-01',
        warningWindowDays: 180,
    });

    assert.deepEqual(result.problems, []);
    assert.equal(result.findings[0].daysUntilEol, 0);
    assert.equal(result.findings[0].status, 'eol');
});

test('aborts the schedule fetch after the configured timeout', async () => {
    const originalFetch = global.fetch;
    // Simulate a stalled endpoint: the promise never settles on its own but
    // honors the abort signal the way the real fetch does.
    global.fetch = (url, opts) =>
        new Promise((resolve, reject) => {
            opts.signal.addEventListener('abort', () => {
                const abortError = new Error('aborted');
                abortError.name = 'AbortError';
                reject(abortError);
            });
        });
    try {
        await assert.rejects(
            scanner.loadSchedule({
                scheduleUrl: 'https://example.invalid/schedule.json',
                fetchTimeoutMs: 20,
            }),
            /timed out after 20ms/,
        );
    } finally {
        global.fetch = originalFetch;
    }
});

test('reports unresolved Azure parameter and macro selector references', () => {
    const repoRoot = makeTempRepo();
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/external-param.yml',
        `
steps:
  - task: UseNode@1
    inputs:
      version: \${{ parameters.nodeVersion }}
`,
    );
    writeFile(
        repoRoot,
        '.azuredevops/pipelines/external-macro.yml',
        `
steps:
  - task: UseNode@1
    inputs:
      version: "$(nodeVersion)"
`,
    );

    const inventory = scanner.collectNodeSelectors(repoRoot);

    // Neither reference resolves from checked-in YAML, so each is reported as a
    // problem instead of being silently dropped, and no selector is invented.
    assert.equal(inventory.problems.length, 2);
    assert(
        inventory.problems.every((problem) =>
            /cannot be verified from checked-in YAML/.test(problem.message),
        ),
    );
    assert.equal(inventory.selectors.length, 0);
});
