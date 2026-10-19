import type { CapacitorConfig } from '@capacitor/cli';

const liveServerUrl = process.env.CAPACITOR_SERVER_URL;

const config: CapacitorConfig = {
  appId: 'io.ionic.starter',
  appName: 'client',
  webDir: 'dist',
  server: liveServerUrl
    ? {
        url: liveServerUrl,
        cleartext: liveServerUrl.startsWith('http://'),
      }
    : undefined,
};

export default config;
