import GamePlaceholderPage from '../../components/game/GamePlaceholderPage';
import { appRoutes } from '../../routing/routes';
import './Story.css';

const Story: React.FC = () => (
  <GamePlaceholderPage
    eyebrow="Chronicle campaign"
    title="Story Mode"
    backRoute={appRoutes.home}
    className="story-page"
  />
);

export default Story;
