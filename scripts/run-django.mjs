import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const repositoryRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const virtualEnvironmentPython = join(
  repositoryRoot,
  '.venv',
  process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python',
);
const python = existsSync(virtualEnvironmentPython)
  ? virtualEnvironmentPython
  : process.platform === 'win32'
    ? 'python'
    : 'python3';

const result = spawnSync(
  python,
  [join(repositoryRoot, 'manage.py'), ...process.argv.slice(2)],
  { cwd: repositoryRoot, stdio: 'inherit' },
);

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
