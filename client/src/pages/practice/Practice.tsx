import { libraryOutline, trophyOutline } from 'ionicons/icons';
import ModeSelectionPage, {
  type ModeSelectionChoice,
} from '../../components/game/ModeSelectionPage';
import { appRoutes } from '../../routing/routes';
import './Practice.css';

const practiceChoices: readonly ModeSelectionChoice[] = [
  {
    route: appRoutes.practiceTopScore,
    title: 'Top Score',
    description: 'Answer without limits. One wrong answer ends the run.',
    meta: 'Endless ladder',
    icon: trophyOutline,
  },
  {
    route: appRoutes.practiceTopics,
    title: 'Choose by Topic',
    description: 'Open the catalogue and train inside a chosen field.',
    meta: 'Focused practice',
    icon: libraryOutline,
  },
];

const Practice: React.FC = () => (
  <ModeSelectionPage
    eyebrow="Solo training"
    title="VS Bot"
    backRoute={appRoutes.home}
    choices={practiceChoices}
    className="practice-page"
  />
);

export default Practice;
