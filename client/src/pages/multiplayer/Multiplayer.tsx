import { peopleCircleOutline, podiumOutline } from 'ionicons/icons';
import ModeSelectionPage, {
  type ModeSelectionChoice,
} from '../../components/game/ModeSelectionPage';
import { appRoutes } from '../../routing/routes';
import './Multiplayer.css';

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
    backRoute={appRoutes.home}
    choices={multiplayerChoices}
    className="multiplayer-page"
  />
);

export default Multiplayer;
