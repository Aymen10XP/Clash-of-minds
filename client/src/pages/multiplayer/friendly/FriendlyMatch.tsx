import GamePlaceholderPage from '../../../components/game/GamePlaceholderPage';
import { appRoutes } from '../../../routing/routes';
import './FriendlyMatch.css';

const FriendlyMatch: React.FC = () => (
  <GamePlaceholderPage
    eyebrow="Private duel"
    title="Friendly Match"
    backRoute={appRoutes.multiplayer}
    className="friendly-match-page"
  />
);

export default FriendlyMatch;
