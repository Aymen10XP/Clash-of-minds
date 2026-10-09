import GamePlaceholderPage from '../../components/game/GamePlaceholderPage';
import { appRoutes } from '../../routing/routes';
import './Settings.css';

const Settings: React.FC = () => (
  <GamePlaceholderPage
    eyebrow="Game preferences"
    title="Settings"
    backRoute={appRoutes.home}
    className="settings-page"
  />
);

export default Settings;
