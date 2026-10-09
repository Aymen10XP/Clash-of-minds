import GamePlaceholderPage from '../../../components/game/GamePlaceholderPage';
import { appRoutes } from '../../../routing/routes';
import './PracticeTopScore.css';

const PracticeTopScore: React.FC = () => (
  <GamePlaceholderPage
    eyebrow="Endless ladder"
    title="Top Score"
    backRoute={appRoutes.practice}
    className="practice-top-score-page"
  />
);

export default PracticeTopScore;
