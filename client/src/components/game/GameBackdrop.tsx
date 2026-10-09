import './GameBackdrop.css';

const particles = [
  'particle--one',
  'particle--two',
  'particle--three',
  'particle--four',
  'particle--five',
] as const;

const GameBackdrop: React.FC = () => (
  <div className="game-backdrop" aria-hidden="true">
    {particles.map((particle) => (
      <span key={particle} className={`game-particle ${particle}`} />
    ))}
    <span className="archive-ring archive-ring--outer" />
    <span className="archive-ring archive-ring--inner" />
    <span className="civilization-frieze civilization-frieze--top" />
    <span className="civilization-frieze civilization-frieze--bottom" />
  </div>
);

export default GameBackdrop;
