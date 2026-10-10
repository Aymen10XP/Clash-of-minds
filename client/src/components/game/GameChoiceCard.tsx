import type { ComponentProps } from 'react';
import { IonIcon, IonItem, IonLabel } from '@ionic/react';
import { checkmarkOutline } from 'ionicons/icons';
import './GameChoiceCard.css';

interface GameChoiceCardProps
  extends Omit<ComponentProps<typeof IonItem>, 'button' | 'children' | 'detail' | 'onClick'> {
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
  ...itemProps
}) => (
  <IonItem
    {...itemProps}
    button
    detail={false}
    aria-label={`${title}: ${description}`}
    className={`game-choice-card${selected ? ' game-choice-card--selected' : ''}${
      compact ? ' game-choice-card--compact' : ''
    } ${className}`.trim()}
    role="button"
    aria-pressed={selected ? 'true' : 'false'}
    onClick={onSelect}
  >
    <span className="game-choice-card__flare" aria-hidden="true" />

    <IonIcon className="game-choice-card__icon" icon={icon} slot="start" aria-hidden="true" />

    <IonLabel className="game-choice-card__content">
      {meta && <span className="game-choice-card__meta">{meta}</span>}
      <span className="game-choice-card__title">{title}</span>
      <span className="game-choice-card__description">{description}</span>
    </IonLabel>

    <span className="game-choice-card__status" slot="end" aria-hidden="true">
      {selected ? <IonIcon icon={checkmarkOutline} /> : <span />}
    </span>
  </IonItem>
);

export default GameChoiceCard;
