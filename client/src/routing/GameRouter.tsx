import { Navigate, Route } from 'react-router-dom';
import { IonRouterOutlet } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { PublicOnly, RequireAuth, RequireStaff } from '../features/auth/AuthGate';
import AdminConsole from '../pages/admin/AdminConsole';
import Login from '../pages/login/Login';
import Register from '../pages/register/Register';
import ForgotPassword from '../pages/forgot-password/ForgotPassword';
import ResetPassword from '../pages/reset-password/ResetPassword';
import Home from '../pages/home/Home';
import Multiplayer from '../pages/multiplayer/Multiplayer';
import FriendlyMatch from '../pages/multiplayer/friendly/FriendlyMatch';
import MatchRoom from '../pages/multiplayer/match/MatchRoom';
import RankedMatchmaking from '../pages/multiplayer/ranked/RankedMatchmaking';
import Practice from '../pages/practice/Practice';
import PracticeTopScore from '../pages/practice/top-score/PracticeTopScore';
import PracticeTopics from '../pages/practice/topics/PracticeTopics';
import Settings from '../pages/settings/Settings';
import Story from '../pages/story/Story';
import { appRoutes } from './routes';

const GameRouter: React.FC = () => (
  <IonReactRouter>
    <IonRouterOutlet animated>
      <Route path={appRoutes.home} element={<RequireAuth><Home /></RequireAuth>} />
      <Route path={appRoutes.login} element={<PublicOnly><Login /></PublicOnly>} />
      <Route path={appRoutes.register} element={<PublicOnly><Register /></PublicOnly>} />
      <Route path={appRoutes.forgotPassword} element={<PublicOnly><ForgotPassword /></PublicOnly>} />
      <Route path={appRoutes.resetPassword} element={<PublicOnly><ResetPassword /></PublicOnly>} />
      <Route path={appRoutes.story} element={<RequireAuth><Story /></RequireAuth>} />
      <Route path={appRoutes.practice} element={<RequireAuth><Practice /></RequireAuth>} />
      <Route path={appRoutes.practiceTopScore} element={<RequireAuth><PracticeTopScore /></RequireAuth>} />
      <Route path={appRoutes.practiceTopScoreTopic} element={<RequireAuth><PracticeTopScore /></RequireAuth>} />
      <Route path={appRoutes.practiceTopics} element={<RequireAuth><PracticeTopics /></RequireAuth>} />
      <Route path={appRoutes.multiplayer} element={<RequireAuth><Multiplayer /></RequireAuth>} />
      <Route path={appRoutes.multiplayerRanked} element={<RequireAuth><RankedMatchmaking /></RequireAuth>} />
      <Route path={appRoutes.multiplayerFriendly} element={<RequireAuth><FriendlyMatch /></RequireAuth>} />
      <Route path={appRoutes.multiplayerMatch} element={<RequireAuth><MatchRoom /></RequireAuth>} />
      <Route path={appRoutes.settings} element={<RequireAuth><Settings /></RequireAuth>} />
      <Route path={appRoutes.admin} element={<RequireStaff><AdminConsole /></RequireStaff>} />
      <Route path={appRoutes.root} element={<Navigate to={appRoutes.home} replace />} />
      <Route path="*" element={<Navigate to={appRoutes.home} replace />} />
    </IonRouterOutlet>
  </IonReactRouter>
);

export default GameRouter;
