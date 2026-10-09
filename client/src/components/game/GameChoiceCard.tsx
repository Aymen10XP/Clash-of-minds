import type { ButtonHTMLAttributes } from 'react';
import { IonIcon } from '@ionic/react';
import { checkmarkOutline } from 'ionicons/icons';
import './GameChoiceCard.css';

interface GameChoiceCardProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children' | 'onClick'> {
  title: string;
  description: string;
  icon: string;
  meta?: string;
  selected?: boolean;
  compact?: boolean;
  onSelect: () => void;
}

const GameChoiceCard: React.FC<GameChoiceCardProps> = ({
  title,
  description,
  icon,
  meta,
  selected = false,
  compact = false,
  onSelect,
  className = '',
  ...buttonProps
}) => (
  <button
    {...buttonProps}
    type="button"
    className={`game-choice-card${selected ? ' game-choice-card--selected' : ''}${
      compact ? ' game-choice-card--compact' : ''
    } ${className}`.trim()}
    aria-pressed={selected}
    onClick={onSelect}
  >
    <span className="game-choice-card__icon" aria-hidden="true">
      <IonIcon icon={icon} />
    </span>

    <span className="game-choice-card__content">
      {meta && <span className="game-choice-card__meta">{meta}</span>}
      <span className="game-choice-card__title">{title}</span>
      <span className="game-choice-card__description">{description}</span>
    </span>

    <span className="game-choice-card__status" aria-hidden="true">
      {selected ? <IonIcon icon={checkmarkOutline} /> : <span />}
    </span>
  </button>
);

export default GameChoiceCard;
