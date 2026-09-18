const assert = require('assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { test, after } = require('node:test');
const yaml = require('yaml');

const scanner = require('../../.github/scripts/check-toolchain-eol.js');

const FIXTURE_SCHEDULE = require('./fixtures/node-schedule.json');

const EXPECTED_TOOLCHAIN_EOL_TEST_SCRIPT = 'node --test tests/toolchain-eol/check-toolchain-eol.test.js';
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

test('package script uses the explicit toolchain EOL test file target', () => {
    const packageJsonPath = path.resolve(__dirname, '..', '..', 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    assert.equal(
        packageJson.scripts['test:toolchain-eol'],
        EXPECTED_TOOLCHAIN_EOL_TEST_SCRIPT,
        [
            'scripts["test:toolchain-eol"] must use the selected explicit-file target',
            `"${EXPECTED_TOOLCHAIN_EOL_TEST_SCRIPT}" and must not be reverted to the bare-directory`,
            '"node --test tests/toolchain-eol/" target; directory recursion was documented in Node v20',
            'and reported as no longer working in Node v21.',
        ].join(' '),
    );
});

test('explicit toolchain EOL npm target covers every test file in this directory', () => {
    const testFiles = fs.readdirSync(__dirname).filter((name) => name.endsWith('.test.js')).sort();

    assert.deepEqual(
        testFiles,
        ['check-toolchain-eol.test.js'],
        [
            'The explicit test:toolchain-eol npm target must cover every tests/toolchain-eol/*.test.js file.',
            'If a new *.test.js file is added, add it to the npm target and this assertion, and review or',
            'update .template-sync/manifest.yml so the new test file has the correct module ownership.',
        ].join(' '),
    );
});

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

function writeNodeWorkflow(repoRoot, inputs, matrix) {
    writeFile(repoRoot, '.github/workflows/node.yml', yaml.stringify({
        jobs: { test: {
            ...(matrix ? { strategy: { matrix } } : {}),
            steps: [{ uses: 'actions/setup-node@v7', with: inputs }],
        } },
    }));
}

const nodeVersionFileCases = [
    ['.nvmrc', '24.18.0\n', '24.18.0'],
    ['.node-version', '24.18.0\n', '24.18.0'],
    ['.tool-versions', 'python 3.13.14\nnodejs 24.18.0\n', '24.18.0'],
    ['.tool-versions', 'node 24.18.0\n', '24.18.0'],
    ['.nvmrc', 'v24.18.0\n', '24.18.0'],
    ['config/package.json', { volta: { node: '22.19.0' }, devEngines: { runtime: { name: 'node', version: '24.18.0' } }, engines: { node: '26.9.0' } }, '22.19.0'],
    ['config/package.json', { devEngines: { runtime: { name: 'NoDe', version: '24.18.0' } }, engines: { node: '26.9.0' } }, '24.18.0'],
    ['config/package.json', { devEngines: { runtime: [{ name: 'python', version: '3.13.14' }, { name: 'node' }, { name: 'NODE', version: '22.19.0' }, { name: 'node', version: '24.18.0' }] }, engines: { node: '26.9.0' } }, '22.19.0'],
    ['config/package.json', { engines: { node: '24.18.0' }, volta: { extends: 'missing.json' } }, '24.18.0'],
    ['config/package.json', { engines: { node: '24' } }, '24'],
    ['config/package.json', { volta: { node: '24.18.0' }, devEngines: { runtime: [null] } }, '24.18.0'],
];

for (const [index, [file, value, expected]] of nodeVersionFileCases.entries()) {
    test(`inventories setup-node file selection ${index}: ${file}`, () => {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, file, typeof value === 'string' ? value : JSON.stringify(value));
        writeNodeWorkflow(repoRoot, { 'node-version-file': file });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => [item.rawValue, item.referencedPath]), [[expected, file]]);
    });
}

test('setup-node inventory follows relative Volta inheritance', () => {
    const repoRoot = makeTempRepo();
    writeFile(repoRoot, 'config/package.json', JSON.stringify({ volta: { extends: '../shared/base.json' } }));
    writeFile(repoRoot, 'shared/base.json', JSON.stringify({ volta: { extends: 'runtime.json' } }));
    writeFile(repoRoot, 'shared/runtime.json', JSON.stringify({ engines: { node: '24.18.0' } }));
    writeNodeWorkflow(repoRoot, { 'node-version-file': 'config/package.json' });
    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);
    assert.deepEqual(inventory.selectors.map((item) => [item.rawValue, item.referencedPath]), [['24.18.0', 'shared/runtime.json']]);
});

test('nonempty direct setup-node input overrides the file; blank direct input permits it', () => {
    for (const [direct, file, expected] of [
        ['24', 'missing.json', '24'],
        ['24', '.nvmrc', '24'],
        ['', '.nvmrc', '22.19.0'],
        ['   ', '.nvmrc', '22.19.0'],
    ]) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, { 'node-version': direct, 'node-version-file': file });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), [expected]);
    }
});

test('setup-node file inventory reports missing, malformed, escaping, and cyclic sources', () => {
    const cases = [
        ['missing.json', undefined, /ENOENT/],
        ['config/package.json', '{', /valid JSON/],
        ['config/package.json', {}, /does not select a string/],
        ['config/package.json', { volta: { node: 24 } }, /does not select a string/],
        ['config/package.json', { devEngines: { runtime: [null] }, engines: { node: '24.18.0' } }, /string name/],
        ['config/package.json', { devEngines: { runtime: { name: 42, version: '24.18.0' } }, engines: { node: '24.18.0' } }, /string name/],
        ['config/package.json', { volta: { extends: 42 } }, /repository-contained/],
        ['config/package.json', { volta: { extends: '../../outside.json' } }, /escapes repository root/],
        ['config/package.json', { volta: { extends: 'package.json' } }, /cyclic/],
        ['.nvmrc', '', /does not select a string/],
    ];
    for (const [file, value, message] of cases) {
        const repoRoot = makeTempRepo();
        if (value !== undefined) {
            writeFile(repoRoot, file, typeof value === 'string' ? value : JSON.stringify(value));
        }
        writeNodeWorkflow(repoRoot, { 'node-version-file': file });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.equal(inventory.selectors.length, 0);
        assert.equal(inventory.problems.length, 1);
        assert.match(inventory.problems[0].message, message);
    }
});

test('setup-node mixed matrix variants retain the literal version-file fallback', () => {
    const cases = [
        [{ node: ['', '24'] }, ['22.19.0', '24']],
        [{ node: [null, '24'] }, ['22.19.0', '24']],
        [{ include: [{ node: ' ' }, { node: '24' }] }, ['22.19.0', '24']],
        [{ node: ['', ' '] }, ['22.19.0']],
        [{ node: ['24', '26'] }, ['24', '26']],
    ];
    for (const [matrix, expected] of cases) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}',
            'node-version-file': expected.includes('22.19.0') ? '.nvmrc' : 'ignored-missing-file',
        }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue).sort(), expected);
    }
});

test('setup-node all-blank direct matrix still inventories file-matrix values', () => {
    const repoRoot = makeTempRepo();
    writeFile(repoRoot, '.nvmrc', '22.19.0\n');
    writeFile(repoRoot, '.node-version', '24.18.0\n');
    writeNodeWorkflow(repoRoot, {
        'node-version': '${{ matrix.node }}',
        'node-version-file': '${{ matrix.file }}',
    }, { node: ['', ' '], file: ['.nvmrc', '.node-version'] });
    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);
    assert.deepEqual(inventory.selectors.map((item) => item.rawValue).sort(), ['22.19.0', '24.18.0']);
});

test('setup-node correlates static pairs and treats missing direct properties as blank', () => {
    for (const [matrix, expected] of [
        [{ include: [{ node: '', file: '.nvmrc' }, { node: '24', file: 'ignored-file' }] }, ['22.19.0', '24']],
        [{ file: ['.nvmrc'] }, ['22.19.0']],
    ]) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}',
            'node-version-file': '${{ matrix.file }}',
        }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), expected);
        assert.deepEqual(inventory.problems, []);
    }
});

test('setup-node reports unresolved consulted version-file matrices', () => {
    for (const matrix of [{}, { file: [] }]) {
        for (const direct of [undefined, '${{ matrix.node }}']) {
            const repoRoot = makeTempRepo();
            writeNodeWorkflow(repoRoot, {
                ...(direct === undefined ? {} : { 'node-version': direct }),
                'node-version-file': '${{ matrix.file }}',
            }, { ...matrix, node: ['', ' '] });
            const inventory = scanner.collectNodeSelectors(repoRoot);
            assert.deepEqual(inventory.selectors, []);
            assert.equal(inventory.problems.length, 1);
            assert.equal(inventory.problems[0].path.split(path.sep).join('/'), '.github/workflows/node.yml');
            assert.match(inventory.problems[0].message, Object.hasOwn(matrix, 'file')
                ? /axis file must be a nonempty static list/ : /version-file input has a blank value/);
        }
    }
});

test('setup-node reports blank consulted version-file values without losing valid files', () => {
    for (const blank of ['', ' ', null]) {
        for (const validFile of [false, true]) {
            const repoRoot = makeTempRepo();
            writeFile(repoRoot, '.nvmrc', '22.19.0\n');
            writeNodeWorkflow(repoRoot, { 'node-version-file': '${{ matrix.file }}' }, {
                file: validFile ? [blank, '.nvmrc'] : [blank],
            });
            const inventory = scanner.collectNodeSelectors(repoRoot);
            assert.deepEqual(inventory.selectors.map((item) => item.rawValue), validFile ? ['22.19.0'] : []);
            assert.equal(inventory.problems.length, 1);
            assert.match(inventory.problems[0].message, /version-file input has a blank value/);
        }
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, { 'node-version-file': blank });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.selectors, []);
        assert.equal(inventory.problems.length, 1);
        assert.match(inventory.problems[0].message, /version-file input has a blank value/);
    }
});

test('setup-node nonblank direct input ignores unresolved or blank version-file inputs', () => {
    for (const file of ['${{ matrix.file }}', '', null]) {
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}',
            'node-version-file': file,
        }, { node: ['24'] });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
    }
});

test('setup-node excludes unreachable blank variants before reading the version file', () => {
    for (const file of ['.nvmrc', 'missing-file']) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '16.0.0\n');
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}', 'node-version-file': file,
        }, { node: ['', '24'], exclude: [{ node: '' }] });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
    }
});

test('setup-node distinguishes partial exclusions, complete removal, and include restoration', () => {
    const cases = [
        [{ os: ['ubuntu', 'windows'], node: ['', '24'], exclude: [{ os: 'ubuntu', node: '' }] }, ['22.19.0', '24']],
        [{ os: ['ubuntu', 'windows'], node: ['', '24'], exclude: [{ node: '' }] }, ['24']],
        [{ node: ['', '24'], exclude: [{ node: '' }], include: [{ node: '' }] }, ['22.19.0', '24']],
        [{ node: [''], exclude: [{ node: '' }] }, []],
        [{ node: [''], exclude: [{ node: '' }], include: [{ node: '24' }] }, ['24']],
    ];
    for (const [matrix, expected] of cases) {
        const repoRoot = makeTempRepo();
        if (expected.includes('22.19.0')) writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}', 'node-version-file': '.nvmrc',
        }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue).sort(), expected);
    }
});

test('setup-node applies ordered includes to original combinations only', () => {
    const repoRoot = makeTempRepo();
    writeFile(repoRoot, '.node-version', '22.19.0\n');
    writeFile(repoRoot, '.nvmrc', '24.18.0\n');
    writeNodeWorkflow(repoRoot, {
        'node-version': '${{ matrix.node }}', 'node-version-file': '${{ matrix.file }}',
    }, {
        os: ['ubuntu'], node: [''],
        include: [
            { file: 'overwritten-missing-file' },
            { os: 'windows', node: '', file: '.nvmrc' },
            { file: '.node-version' },
        ],
    });
    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);
    assert.deepEqual(inventory.selectors.map((item) => [item.rawValue, item.referencedPath]), [
        ['22.19.0', '.node-version'], ['24.18.0', '.nvmrc'],
    ]);
});

test('setup-node resolves nested object axes and compares excluded objects structurally', () => {
    const repoRoot = makeTempRepo();
    writeNodeWorkflow(repoRoot, {
        'node-version': '${{ matrix.node.version }}', 'node-version-file': 'missing-file',
    }, {
        node: [{ version: '', env: 'test' }, { version: '24' }],
        exclude: [{ node: { env: 'test', version: '' } }],
    });
    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);
    assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
});

test('setup-node reports missing direct matrix properties without a file fallback', () => {
    const cases = [
        [undefined, '${{ matrix.node }}', []],
        [{ os: ['ubuntu'] }, '${{ matrix.node }}', []],
        [{ node: [{}] }, '${{ matrix.node.version }}', []],
        [{ node: [null] }, '${{ matrix.node.version }}', []],
        [{ include: [{ os: 'ubuntu' }, { os: 'windows', node: '24' }] }, '${{ matrix.node }}', ['24']],
        [{ os: ['ubuntu', 'windows'] }, '${{ matrix.node }}', []],
    ];
    for (const [matrix, direct, expected] of cases) {
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, { 'node-version': direct }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), expected);
        assert.equal(inventory.problems.length, 1);
        assert.match(inventory.problems[0].message, /direct matrix input matrix\.node(?:\.version)? is missing.*no version-file fallback/);
        assert.equal(inventory.problems[0].path.split(path.sep).join('/'), '.github/workflows/node.yml');
    }
});

test('setup-node preserves missing-property fallback and excluded combinations', () => {
    for (const file of ['.nvmrc', '${{ matrix.file }}']) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}', 'node-version-file': file },
            { file: ['.nvmrc'] });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['22.19.0']);
    }
    const repoRoot = makeTempRepo();
    writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}' },
        { os: ['ubuntu'], exclude: [{ os: 'ubuntu' }] });
    assert.deepEqual(scanner.collectNodeSelectors(repoRoot), { selectors: [], problems: [] });
});

test('setup-node preserves explicit empty matrix and auth-only inputs', () => {
    for (const empty of ['', ' ', null]) {
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}' }, { node: [empty, '24'] });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
        writeNodeWorkflow(repoRoot, { 'node-version': empty });
        assert.deepEqual(scanner.collectNodeSelectors(repoRoot), { selectors: [], problems: [] });
    }
    const repoRoot = makeTempRepo();
    writeNodeWorkflow(repoRoot, { 'registry-url': 'https://registry.npmjs.org' });
    assert.deepEqual(scanner.collectNodeSelectors(repoRoot), { selectors: [], problems: [] });
});

test('missing matrix diagnostic oracle detects assertion removal', () => {
    const repoRoot = makeTempRepo();
    writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}' },
        { include: [{ os: 'ubuntu' }, { os: 'windows', node: '24' }] });
    const baseline = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(baseline.selectors.map((item) => item.rawValue), ['24']);
    assert.equal(baseline.problems.length, 1);
    const original = fs.readFileSync(path.resolve(__dirname, '../../.github/scripts/check-toolchain-eol.js'), 'utf8');
    const predicate = 'if (resolved.missingProperty)';
    assert.equal(original.split(predicate).length - 1, 1);
    const mutant = path.join(repoRoot, 'scanner-mutant.js');
    fs.writeFileSync(mutant, original.replace(predicate, 'if (false)'));
    const child = spawnSync(process.execPath, ['-e', `
        const assert = require('assert/strict');
        const inventory = require(process.argv[1]).collectNodeSelectors(process.argv[2]);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
        assert.equal(inventory.problems.length, 1, 'A valid sibling must not hide missing selection.');
    `, mutant, repoRoot], {
        encoding: 'utf8', timeout: 30000,
        env: { ...process.env, NODE_PATH: path.resolve(__dirname, '../../node_modules') },
    });
    assert.ifError(child.error);
    assert.equal(child.status, 1);
    assert.match(child.stderr, /AssertionError/);
    assert.match(child.stderr, /A valid sibling must not hide missing selection/);
});

test('setup-node static matrix diagnostics retain unknown and malformed inputs', () => {
    const cases = [
        ['${{ fromJSON(needs.build.outputs.matrix) }}', /static matrix mapping/],
        [{ node: '${{ needs.build.outputs.versions }}' }, /dynamic/],
        [{ node: ['${{ vars.NODE }}'] }, /dynamic/],
        [{ node: ['24'], include: {} }, /include must be a list/],
        [{ node: ['24'], exclude: [null] }, /exclude must be a list/],
        [{ node: [{ version: '24' }] }, /must be scalar/],
        [{ node: ['24'], os: [] }, /nonempty static list/],
    ];
    for (const [matrix, message] of cases) {
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}' }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.selectors, []);
        assert.equal(inventory.problems.length, 1);
        assert.match(inventory.problems[0].message, message);
        assert.equal(inventory.problems[0].path.split(path.sep).join('/'), '.github/workflows/node.yml');
    }
});

test('setup-node matrix limits apply separately before and after exclusions', () => {
    const cases = [
        [{ node: ['24'], job: Array.from({ length: 256 }, (_, i) => i) }, null],
        [{ node: ['24'], job: Array.from({ length: 257 }, (_, i) => i) }, /256-job/],
        [{ node: ['24'], os: ['keep', 'remove'], job: Array.from({ length: 256 }, (_, i) => i), exclude: [{ os: 'remove' }] }, null],
        [{ node: ['24'], job: Array.from({ length: 4097 }, (_, i) => i), exclude: [{}] }, /4096-combination/],
        [{ include: Array.from({ length: 257 }, (_, i) => ({ node: '24', job: i })) }, /256-job/],
    ];
    for (const [matrix, message] of cases) {
        const repoRoot = makeTempRepo();
        writeNodeWorkflow(repoRoot, { 'node-version': '${{ matrix.node }}' }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        if (message) {
            assert.deepEqual(inventory.selectors, []);
            assert.equal(inventory.problems.length, 1);
            assert.match(inventory.problems[0].message, message);
        } else {
            assert.deepEqual(inventory.problems, []);
            assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
        }
    }
});

test('setup-node literal direct input ignores an unrelated dynamic matrix', () => {
    const repoRoot = makeTempRepo();
    writeNodeWorkflow(repoRoot, { 'node-version': '24', 'node-version-file': 'missing-file' },
        '${{ fromJSON(needs.build.outputs.matrix) }}');
    const inventory = scanner.collectNodeSelectors(repoRoot);
    assert.deepEqual(inventory.problems, []);
    assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24']);
});

test('setup-node matrix regression oracles fail when exclusion or correlation is removed', () => {
    const originalPath = path.resolve(__dirname, '../../.github/scripts/check-toolchain-eol.js');
    const original = fs.readFileSync(originalPath, 'utf8');
    const cases = [
        [
            /originals = originals\.filter\([\s\S]*?matrixValuesEqual\(entry\[key\], value\)\)\)\);/,
            'originals = originals;',
            { node: ['', '24'], exclude: [{ node: '' }] }, ['24'],
        ],
        [
            /resolveGithubExpression\(file, combination\)/,
            'resolveGithubExpression(file, combinations[0])',
            { include: [{ node: '24', file: 'ignored-file' }, { node: '', file: '.nvmrc' }] }, ['24', '22.19.0'],
        ],
    ];
    for (const [pattern, replacement, matrix, expected] of cases) {
        const repoRoot = makeTempRepo();
        writeFile(repoRoot, '.nvmrc', '22.19.0\n');
        writeNodeWorkflow(repoRoot, {
            'node-version': '${{ matrix.node }}',
            'node-version-file': Object.hasOwn(matrix, 'include') ? '${{ matrix.file }}' : '.nvmrc',
        }, matrix);
        const inventory = scanner.collectNodeSelectors(repoRoot);
        assert.deepEqual(inventory.problems, []);
        assert.deepEqual(inventory.selectors.map((item) => item.rawValue), expected);
        assert.match(original, pattern);
        const mutant = path.join(repoRoot, 'scanner-mutant.js');
        fs.writeFileSync(mutant, original.replace(pattern, replacement));
        const child = spawnSync(process.execPath, ['-e', `
            const assert = require('assert/strict');
            const inventory = require(process.argv[1]).collectNodeSelectors(process.argv[2]);
            assert.deepEqual(inventory.problems, []);
            assert.deepEqual(inventory.selectors.map((item) => item.rawValue), JSON.parse(process.argv[3]));
        `, mutant, repoRoot, JSON.stringify(expected)], {
            encoding: 'utf8', timeout: 30000,
            env: { ...process.env, NODE_PATH: path.resolve(__dirname, '../../node_modules') },
        });
        assert.equal(child.error, undefined);
        assert.equal(child.status, 1);
        assert.match(child.stderr, /AssertionError/);
    }
});

test('setup-node inventory accepts 32 inherited files and reports a longer chain', () => {
    for (const count of [32, 33]) {
        const repoRoot = makeTempRepo();
        for (let index = 0; index < count; index += 1) {
            writeFile(repoRoot, `config/${index}.json`, JSON.stringify(index + 1 === count
                ? { engines: { node: '24.18.0' } }
                : { volta: { extends: `${index + 1}.json` } }));
        }
        writeNodeWorkflow(repoRoot, { 'node-version-file': 'config/0.json' });
        const inventory = scanner.collectNodeSelectors(repoRoot);
        if (count === 32) {
            assert.deepEqual(inventory.problems, []);
            assert.deepEqual(inventory.selectors.map((item) => item.rawValue), ['24.18.0']);
        } else {
            assert.equal(inventory.selectors.length, 0);
            assert.equal(inventory.problems.length, 1);
            assert.match(inventory.problems[0].message, /32-file/);
        }
    }
});

const yamlGuidePath = path.resolve(__dirname, '..', '..', '.github/instructions/yaml.instructions.md');
const optionalYamlGuide = { skip: !fs.existsSync(yamlGuidePath) && 'Optional YAML guide is excluded.' };

function documentedNodeExample() {
    const guide = fs.readFileSync(yamlGuidePath, 'utf8');
    const section = guide.split(/### Exact Node\.js version-file exception\r?\n/)[1]
        .split(/\r?\n## GitHub Actions Documentation Comment URLs/)[0];
    const manifest = JSON.parse(section.match(/```json\r?\n([\s\S]*?)\r?\n```/)[1]);
    const steps = yaml.parse(section.match(/```yaml\r?\n([\s\S]*?)\r?\n```/)[1]);
    return { manifest, steps };
}

function assertDocumentedNodeExample(manifest, steps) {
    // A narrow oracle for this documented example, not an arbitrary-workflow validator.
    assert.deepEqual(Object.keys(manifest), ['engines']);
    assert.match(manifest.engines.node, /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/);
    const setup = steps.findIndex((step) => step.uses && step.uses.startsWith('actions/setup-node@'));
    const verify = steps.findIndex((step) => step.name === 'Verify the exact Node.js runtime');
    const install = steps.findIndex((step) => step.run === 'npm ci');
    assert(setup >= 0 && verify > setup && install > verify);
    assert.equal(steps[setup].with['node-version-file'], 'package.json');
    assert(!Object.hasOwn(steps[setup].with, 'node-version'));
    assert.equal(steps[setup].with['package-manager-cache'], false);
    assert.equal(steps[verify].shell, 'bash');
    assert.match(steps[verify].run, /readFileSync\('package\.json', 'utf8'\)\)\.engines\.node/);
    assert.match(steps[verify].run, /process\.versions\.node !== expected/);
}

test('documented Node file example preserves selection and verification order', optionalYamlGuide, () => {
    const { manifest, steps } = documentedNodeExample();
    assertDocumentedNodeExample(manifest, steps);
    const mutations = [
        (m) => { m.engines.node = '24'; },
        (m) => { m.engines.node = '24.x'; },
        (m) => { m.engines.node = '>=24'; },
        (m) => { m.engines.node = 'lts/*'; },
        (m) => { m.engines.node = '24.18.0-rc.1'; },
        (m) => { m.engines.node = '24.18.0+build'; },
        (m, s) => { s[1].with['node-version'] = '24'; },
        (m, s) => { s[2].run = s[2].run.replace('.engines.node', '.volta.node'); },
        (m, s) => { s[2].run = 'node --version'; },
        (m, s) => { [s[2], s[3]] = [s[3], s[2]]; },
    ];
    for (const mutate of mutations) {
        const changed = structuredClone({ manifest, steps });
        mutate(changed.manifest, changed.steps);
        assert.throws(() => assertDocumentedNodeExample(changed.manifest, changed.steps));
    }
});

test('documented Node verifier executes and rejects mismatched or non-exact values', optionalYamlGuide, () => {
    const { steps } = documentedNodeExample();
    const verification = steps.find((step) => step.name === 'Verify the exact Node.js runtime');
    const script = verification.run.match(/^node <<'NODE'\n([\s\S]*)\nNODE\n?$/)[1];
    const repoRoot = makeTempRepo();
    // Use the executing runtime for a portable success; the published pin is illustrative.
    const cases = [
        [process.versions.node, 0],
        ['0.0.0', 1],
        ['24', 1],
        ['24.x', 1],
        ['>=24', 1],
        ['lts/*', 1],
        ['24.18.0-rc.1', 1],
        ['24.18.0+build', 1],
    ];
    for (const [expected, exitCode] of cases) {
        writeFile(repoRoot, 'package.json', JSON.stringify({ engines: { node: expected } }));
        const result = spawnSync(process.execPath, ['-e', script], { cwd: repoRoot, encoding: 'utf8', timeout: 10000 });
        assert.ifError(result.error);
        assert.equal(result.status, exitCode, result.stderr);
        if (exitCode !== 0) {
            assert.match(result.stderr, /Expected Node.js/);
        }
    }
});
