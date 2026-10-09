import { useNavigate } from 'react-router-dom';
import GameSubpage from '../components/game/GameSubpage';
import { playUiFeedback } from '../lib/uiFeedback';
import { appRoutes } from '../routing/routes';

const RankedMatchmaking: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    playUiFeedback('light');
    navigate(appRoutes.multiplayer);
  };

  return <GameSubpage eyebrow="Competitive duel" title="Ranked Matchmaking" onBack={handleBack} />;
};

export default RankedMatchmaking;
