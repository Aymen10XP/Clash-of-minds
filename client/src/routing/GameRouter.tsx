import { Navigate, Route } from 'react-router-dom';
import { IonRouterOutlet } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import Home from '../pages/home/Home';
import Multiplayer from '../pages/multiplayer/Multiplayer';
import FriendlyMatch from '../pages/multiplayer/friendly/FriendlyMatch';
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
      <Route path={appRoutes.home} element={<Home />} />
      <Route path={appRoutes.story} element={<Story />} />
      <Route path={appRoutes.practice} element={<Practice />} />
      <Route path={appRoutes.practiceTopScore} element={<PracticeTopScore />} />
      <Route path={appRoutes.practiceTopics} element={<PracticeTopics />} />
      <Route path={appRoutes.multiplayer} element={<Multiplayer />} />
      <Route path={appRoutes.multiplayerRanked} element={<RankedMatchmaking />} />
      <Route path={appRoutes.multiplayerFriendly} element={<FriendlyMatch />} />
      <Route path={appRoutes.settings} element={<Settings />} />
      <Route path={appRoutes.root} element={<Navigate to={appRoutes.home} replace />} />
      <Route path="*" element={<Navigate to={appRoutes.home} replace />} />
    </IonRouterOutlet>
  </IonReactRouter>
);

export default GameRouter;
