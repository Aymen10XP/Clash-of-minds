import { Navigate, Route } from 'react-router-dom';
import { IonApp, IonRouterOutlet, setupIonicReact } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import Home from './pages/Home';
import FriendlyMatch from './pages/FriendlyMatch';
import Multiplayer from './pages/Multiplayer';
import PracticeTopics from './pages/PracticeTopics';
import PracticeTopScore from './pages/PracticeTopScore';
import RankedMatchmaking from './pages/RankedMatchmaking';
import VsBot from './pages/VsBot';
import { appRoutes } from './routing/routes';

/* Core CSS required for Ionic components to work properly */
import '@ionic/react/css/core.css';

/* Basic CSS for apps built with Ionic */
import '@ionic/react/css/normalize.css';
import '@ionic/react/css/structure.css';
import '@ionic/react/css/typography.css';

/* Optional CSS utils that can be commented out */
import '@ionic/react/css/padding.css';
import '@ionic/react/css/float-elements.css';
import '@ionic/react/css/text-alignment.css';
import '@ionic/react/css/text-transformation.css';
import '@ionic/react/css/flex-utils.css';
import '@ionic/react/css/display.css';

/**
 * Ionic Dark Mode
 * -----------------------------------------------------
 * For more info, please see:
 * https://ionicframework.com/docs/theming/dark-mode
 */

/* import '@ionic/react/css/palettes/dark.always.css'; */
/* import '@ionic/react/css/palettes/dark.class.css'; */
import '@ionic/react/css/palettes/dark.system.css';

/* Theme variables */
import './theme/variables.css';

setupIonicReact();

const App: React.FC = () => (
  <IonApp>
    <IonReactRouter>
      <IonRouterOutlet>
        <Route path={appRoutes.home} element={<Home />} />
        <Route path={appRoutes.practice} element={<VsBot />} />
        <Route path={appRoutes.practiceTopScore} element={<PracticeTopScore />} />
        <Route path={appRoutes.practiceTopics} element={<PracticeTopics />} />
        <Route path={appRoutes.multiplayer} element={<Multiplayer />} />
        <Route path={appRoutes.multiplayerRanked} element={<RankedMatchmaking />} />
        <Route path={appRoutes.multiplayerFriendly} element={<FriendlyMatch />} />
        <Route path={appRoutes.root} element={<Navigate to={appRoutes.home} replace />} />
      </IonRouterOutlet>
    </IonReactRouter>
  </IonApp>
);

export default App;
