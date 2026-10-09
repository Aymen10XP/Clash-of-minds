import { useNavigate } from 'react-router-dom';
import GameSubpage from '../components/game/GameSubpage';
import { playUiFeedback } from '../lib/uiFeedback';
import { appRoutes } from '../routing/routes';

const PracticeTopScore: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    playUiFeedback('light');
    navigate(appRoutes.practice);
  };

  return <GameSubpage eyebrow="Endless ladder" title="Top Score" onBack={handleBack} />;
};

export default PracticeTopScore;
