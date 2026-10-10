import { existsSync } from 'node:fs';
import { networkInterfaces } from 'node:os';
import { dirname, join } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
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
const vite = join(repositoryRoot, 'node_modules', 'vite', 'bin', 'vite.js');

const networkAddresses = Object.values(networkInterfaces())
  .flat()
  .filter((address) => address?.family === 'IPv4' && !address.internal)
  .map((address) => address.address);
const allowedHosts = ['localhost', '127.0.0.1', ...networkAddresses];
const trustedOrigins = allowedHosts.flatMap((host) => [
  `http://${host}:5173`,
  `http://${host}:8000`,
]);

const django = spawn(python, ['manage.py', 'runserver', '0.0.0.0:8000'], {
  cwd: repositoryRoot,
  env: {
    ...process.env,
    DJANGO_ALLOWED_HOSTS: allowedHosts.join(','),
    DJANGO_CSRF_TRUSTED_ORIGINS: trustedOrigins.join(','),
  },
  stdio: 'inherit',
});

const client = spawn(
  process.execPath,
  [vite, '--host', '0.0.0.0', '--port', '5173', '--strictPort'],
  { cwd: join(repositoryRoot, 'client'), stdio: 'inherit' },
);

console.log('\nClash of Minds development servers');
console.log('  Client local:  http://localhost:5173');
console.log('  Django local:  http://localhost:8000');
for (const address of networkAddresses) {
  console.log(`  Client network: http://${address}:5173`);
  console.log(`  Django network: http://${address}:8000`);
}
console.log('\nPress Ctrl+C to stop both servers.\n');

let stopping = false;

const stopChild = (child) => {
  if (!child.pid || child.exitCode !== null) return;

  if (isWindows) {
    spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
  } else {
    child.kill('SIGTERM');
  }
};

const stopAll = (exitCode = 0) => {
  if (stopping) return;
  stopping = true;
  stopChild(client);
  stopChild(django);
  process.exit(exitCode);
};

django.on('error', (error) => {
  console.error(`Unable to start Django: ${error.message}`);
  stopAll(1);
});

client.on('error', (error) => {
  console.error(`Unable to start Vite: ${error.message}`);
  stopAll(1);
});

django.on('exit', (code) => stopAll(code ?? 1));
client.on('exit', (code) => stopAll(code ?? 1));
process.on('SIGINT', () => stopAll());
process.on('SIGTERM', () => stopAll());
