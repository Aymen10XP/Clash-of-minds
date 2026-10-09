import { useNavigate } from 'react-router-dom';
import GameSubpage from '../components/game/GameSubpage';
import { playUiFeedback } from '../lib/uiFeedback';
import { appRoutes } from '../routing/routes';

const FriendlyMatch: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    playUiFeedback('light');
    navigate(appRoutes.multiplayer);
  };

  return <GameSubpage eyebrow="Private duel" title="Friendly Match" onBack={handleBack} />;
};

export default FriendlyMatch;
