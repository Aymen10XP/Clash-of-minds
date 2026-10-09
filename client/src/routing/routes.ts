export const appRoutes = {
  root: '/',
  home: '/home',
  login: '/login',
  register: '/register',
  story: '/story',
  practice: '/practice',
  practiceTopScore: '/practice/top-score',
  practiceTopics: '/practice/topics',
  multiplayer: '/multiplayer',
  multiplayerRanked: '/multiplayer/ranked',
  multiplayerFriendly: '/multiplayer/friendly',
  settings: '/settings',
} as const;

export type AppRoute = (typeof appRoutes)[keyof typeof appRoutes];
