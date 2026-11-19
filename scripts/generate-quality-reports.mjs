import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const reportsRoot = join(repositoryRoot, 'reports', 'generated');
const isWindows = process.platform === 'win32';
const npm = isWindows ? 'npm.cmd' : 'npm';
const python = join(
  repositoryRoot,
  '.venv',
  isWindows ? 'Scripts' : 'bin',
  isWindows ? 'python.exe' : 'python',
);

if (!existsSync(python)) {
  throw new Error('Create .venv and install server/requirements-dev.txt before generating evidence.');
}

mkdirSync(reportsRoot, { recursive: true });
mkdirSync(join(reportsRoot, 'coverage'), { recursive: true });
mkdirSync(join(reportsRoot, 'security'), { recursive: true });
mkdirSync(join(reportsRoot, 'tests'), { recursive: true });

const results = [];

function run(name, command, args, options = {}) {
  const startedAt = new Date();
  const execution = spawnSync(command, args, {
    cwd: options.cwd ?? repositoryRoot,
    encoding: 'utf8',
    env: { ...process.env, FORCE_COLOR: '0' },
    shell: isWindows && command === npm,
    maxBuffer: 20 * 1024 * 1024,
  });
  const output = `${execution.stdout ?? ''}${execution.stderr ?? ''}`;
  if (options.logFile) writeFileSync(join(reportsRoot, options.logFile), output, 'utf8');
  const exitCode = execution.status ?? 1;
  const accepted = (options.acceptExitCodes ?? [0]).includes(exitCode);
  results.push({
    name,
    command: [command, ...args].join(' '),
    exitCode,
    accepted,
    startedAt: startedAt.toISOString(),
    durationMs: Date.now() - startedAt.getTime(),
  });
  if (!accepted) {
    const reason = execution.error ? ` (${execution.error.message})` : '';
    throw new Error(`${name} failed with exit code ${exitCode}${reason}. See ${options.logFile}.`);
  }
  return output;
}

run('Client unit tests', npm, [
  'run', 'test', '--workspace', '@mind-clash/client', '--',
  '--reporter=default', '--reporter=junit',
  '--outputFile.junit=../reports/generated/tests/client-junit.xml',
], { logFile: 'tests/client-tests.log' });

run('Backend tests with coverage', python, [
  '-m', 'coverage', 'run', 'manage.py', 'test', '--settings=server.test_settings',
], { logFile: 'tests/backend-tests.log' });
run('Backend coverage XML', python, [
  '-m', 'coverage', 'xml', '-o', join(reportsRoot, 'coverage', 'backend-coverage.xml'),
]);
run('Backend coverage summary', python, ['-m', 'coverage', 'report'], {
  logFile: 'coverage/backend-coverage.txt',
});

run('ESLint static analysis', npm, [
  'exec', '--workspace', '@mind-clash/client', '--', 'eslint', '.',
  '--format', 'json', '--output-file', '../reports/generated/security/eslint.json',
]);
run('Bandit SAST', python, [
  '-m', 'bandit', '-r', 'accounts', 'quiz', 'multiplayer', 'server',
  '-ll', '-ii', '-f', 'json', '-o', join(reportsRoot, 'security', 'bandit.json'),
]);

const npmAudit = run('npm dependency audit', npm, ['audit', '--json'], {
  acceptExitCodes: [0, 1],
});
writeFileSync(join(reportsRoot, 'security', 'npm-audit.json'), npmAudit, 'utf8');
run('Python runtime dependency audit', python, [
  '-m', 'pip_audit', '-r', 'server/requirements.txt', '-f', 'json',
  '-o', join(reportsRoot, 'security', 'pip-audit-runtime.json'),
]);
run('Python development dependency audit', python, [
  '-m', 'pip_audit', '-r', 'server/requirements-dev.txt', '-f', 'json',
  '-o', join(reportsRoot, 'security', 'pip-audit-dev.json'),
]);

run('Django deployment checks', python, ['manage.py', 'check'], {
  logFile: 'django-check.log',
});
run('Migration drift check', python, [
  'manage.py', 'makemigrations', '--check', '--dry-run', '--settings=server.test_settings',
], {
  logFile: 'migration-check.log',
});
run('Client production build', npm, ['run', 'build', '--workspace', '@mind-clash/client'], {
  logFile: 'client-build.log',
});

if (process.argv.includes('--include-e2e')) {
  run('Cypress Chrome and Firefox compatibility', npm, ['run', 'test:e2e:compatibility'], {
    logFile: 'tests/cypress-compatibility.log',
  });
}

const summary = {
  generatedAt: new Date().toISOString(),
  platform: `${process.platform}-${process.arch}`,
  node: process.version,
  successful: results.every((result) => result.accepted),
  results,
};
writeFileSync(join(reportsRoot, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`, 'utf8');
console.log(`Generated ${results.length} reports in ${reportsRoot}`);
