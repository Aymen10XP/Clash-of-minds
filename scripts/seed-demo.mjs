import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const virtualEnvironmentPython = join(
  repositoryRoot,
  '.venv',
  isWindows ? 'Scripts' : 'bin',
  isWindows ? 'python.exe' : 'python',
);
const python = existsSync(virtualEnvironmentPython)
  ? virtualEnvironmentPython
  : isWindows
    ? 'python'
    : 'python3';
const commandArguments = process.argv.slice(2);
const skipDatabaseStart = commandArguments.includes('--skip-db-start');
const seedArguments = commandArguments.filter((argument) => argument !== '--skip-db-start');

const run = (command, args, label) => {
  console.log(`\n${label}`);
  const result = spawnSync(command, args, { cwd: repositoryRoot, stdio: 'inherit' });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
};

if (!skipDatabaseStart) {
  run('docker', ['compose', 'up', '-d', '--wait', 'postgres'], 'Starting PostgreSQL...');
}

run(python, ['manage.py', 'migrate', '--noinput'], 'Applying database migrations...');
run(python, ['manage.py', 'seed_demo', ...seedArguments], 'Creating demo accounts and quiz data...');
