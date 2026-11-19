import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const clientDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../client');
const repositoryRoot = path.dirname(clientDir);
const baseUrl = 'http://127.0.0.1:5173';
const viteBin = path.resolve(path.dirname(require.resolve('vite')), '../../bin/vite.js');
const cypressBin = path.resolve(path.dirname(require.resolve('cypress')), 'bin/cypress');
const cypressVersion = require('cypress/package.json').version;
const cypressArgs = process.argv.slice(2).filter((argument) => argument !== '--docker');
const useDocker = process.argv.includes('--docker');
const children = new Set();

function start(command, args, env = process.env) {
  const child = spawn(command, args, {
    cwd: clientDir,
    env,
    stdio: 'inherit',
  });
  children.add(child);
  child.once('exit', () => children.delete(child));
  return child;
}

function stopChildren() {
  for (const child of children) child.kill();
}

process.on('SIGINT', () => {
  stopChildren();
  process.exitCode = 130;
});
process.on('SIGTERM', () => {
  stopChildren();
  process.exitCode = 143;
});

async function waitForVite(child) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error('Vite exited before Cypress could start.');
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch {
      // Vite is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite did not respond at ${baseUrl} within 30 seconds.`);
}

let portOccupied = false;
try {
  await fetch(baseUrl);
  portOccupied = true;
} catch {
  // Nothing is serving the dedicated E2E port yet.
}
if (portOccupied) {
  console.error(`Port 5173 is already in use. Stop that server before running Cypress.`);
  process.exit(1);
}

const viteEnv = useDocker
  ? { ...process.env, __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS: 'host.docker.internal' }
  : process.env;
const vite = start(process.execPath, [viteBin, '--host', '127.0.0.1', '--port', '5173', '--strictPort'], viteEnv);
try {
  await waitForVite(vite);
  let cypress;
  if (useDocker) {
    const screenshots = path.join(repositoryRoot, '.tmp', 'cypress-screenshots');
    mkdirSync(screenshots, { recursive: true });
    const mounts = [
      [path.join(clientDir, 'cypress'), '/e2e/cypress'],
      [path.join(clientDir, 'cypress.config.ts'), '/e2e/cypress.config.ts'],
      [path.join(clientDir, 'tsconfig.json'), '/e2e/tsconfig.json'],
      [path.join(clientDir, 'tsconfig.node.json'), '/e2e/tsconfig.node.json'],
    ];
    const dockerArgs = [
      'run', '--rm', '-w', '/e2e',
      ...(process.platform === 'linux' ? ['--add-host', 'host.docker.internal:host-gateway'] : []),
      ...mounts.flatMap(([source, target]) => ['-v', `${source}:${target}:ro`]),
      '-v', `${screenshots}:/tmp/cypress-screenshots`,
      `cypress/included:${cypressVersion}`,
      '--config', 'baseUrl=http://host.docker.internal:5173,screenshotsFolder=/tmp/cypress-screenshots,video=false',
      ...cypressArgs,
    ];
    cypress = start('docker', dockerArgs);
  } else {
    const cypressEnv = { ...process.env };
    // Electron hosts can export this for their own child processes.
    delete cypressEnv.ELECTRON_RUN_AS_NODE;
    cypress = start(process.execPath, [cypressBin, 'run', ...cypressArgs], cypressEnv);
  }
  const exitCode = await new Promise((resolve, reject) => {
    cypress.once('error', reject);
    cypress.once('exit', (code, signal) => resolve(signal ? 1 : code ?? 1));
  });
  process.exitCode = exitCode;
} catch (error) {
  console.error(error);
  process.exitCode = 1;
} finally {
  stopChildren();
}
