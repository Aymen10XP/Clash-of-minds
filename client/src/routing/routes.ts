export const appRoutes = {
  root: '/',
  home: '/home',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password/:uid/:token',
  story: '/story',
  practice: '/practice',
  practiceTopScore: '/practice/top-score',
  practiceTopScoreTopic: '/practice/top-score/:topicSlug',
  practiceTopics: '/practice/topics',
  multiplayer: '/multiplayer',
  multiplayerRanked: '/multiplayer/ranked',
  multiplayerFriendly: '/multiplayer/friendly',
  multiplayerMatch: '/multiplayer/match/:matchId',
  settings: '/settings',
  admin: '/admin-console',
} as const;

export type AppRoute = (typeof appRoutes)[keyof typeof appRoutes];
