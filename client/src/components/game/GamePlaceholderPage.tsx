import GameSubpage from './GameSubpage';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import type { AppRoute } from '../../routing/routes';

interface GamePlaceholderPageProps {
  eyebrow: string;
  title: string;
  backRoute: AppRoute;
  className: string;
}

const GamePlaceholderPage: React.FC<GamePlaceholderPageProps> = ({
  eyebrow,
  title,
  backRoute,
  className,
}) => {
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });

  return (
    <GameSubpage
      eyebrow={eyebrow}
      title={title}
      onBack={() => goBackAfterPress(backRoute)}
      className={className}
    />
  );
};

export default GamePlaceholderPage;
