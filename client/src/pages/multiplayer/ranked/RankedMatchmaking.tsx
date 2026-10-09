import GamePlaceholderPage from '../../../components/game/GamePlaceholderPage';
import { appRoutes } from '../../../routing/routes';
import './RankedMatchmaking.css';

const RankedMatchmaking: React.FC = () => (
  <GamePlaceholderPage
    eyebrow="Competitive duel"
    title="Ranked Matchmaking"
    backRoute={appRoutes.multiplayer}
    className="ranked-matchmaking-page"
  />
);

export default RankedMatchmaking;
