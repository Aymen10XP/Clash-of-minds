import type { PropsWithChildren } from 'react';
import GamePage from './GamePage';
import GameScreenHeader from './GameScreenHeader';
import './GameSubpage.css';

type GameSubpageProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  onBack: () => void;
  className?: string;
}>;

const GameSubpage: React.FC<GameSubpageProps> = ({ children, eyebrow, title, onBack, className = '' }) => (
  <GamePage className={className}>
    <main className="game-subpage">
      <GameScreenHeader eyebrow={eyebrow} title={title} onBack={onBack} />
      {children}
    </main>
  </GamePage>
);

export default GameSubpage;
