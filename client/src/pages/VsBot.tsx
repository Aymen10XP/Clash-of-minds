import { libraryOutline, trophyOutline } from 'ionicons/icons';
import ModeSelectionPage, { type ModeSelectionChoice } from '../components/game/ModeSelectionPage';
import { appRoutes } from '../routing/routes';

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

const VsBot: React.FC = () => (
  <ModeSelectionPage
    eyebrow="Solo training"
    title="VS Bot"
    kicker="Choose your trial"
    heading="How will you challenge the archive?"
    description="Climb until your first mistake, or master one field at a time."
    backRoute={appRoutes.home}
    choices={practiceChoices}
  />
);

export default VsBot;
