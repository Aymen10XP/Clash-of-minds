import { peopleCircleOutline, podiumOutline } from 'ionicons/icons';
import ModeSelectionPage, { type ModeSelectionChoice } from '../components/game/ModeSelectionPage';
import { appRoutes } from '../routing/routes';

const multiplayerChoices: readonly ModeSelectionChoice[] = [
  {
    route: appRoutes.multiplayerRanked,
    title: 'Ranked Matchmaking',
    description: 'Enter the queue and face an opponent near your rank.',
    meta: 'Competitive duel',
    icon: podiumOutline,
  },
  {
    route: appRoutes.multiplayerFriendly,
    title: 'Friendly Match',
    description: 'Challenge a friend without affecting your competitive rank.',
    meta: 'Private duel',
    icon: peopleCircleOutline,
  },
];

const Multiplayer: React.FC = () => (
  <ModeSelectionPage
    eyebrow="Online arena"
    title="Multiplayer"
    kicker="Choose your contest"
    heading="How will you enter the arena?"
    description="Test your knowledge for rank, or open a private duel with a friend."
    backRoute={appRoutes.home}
    choices={multiplayerChoices}
  />
);

export default Multiplayer;
