import { IonButton, IonIcon } from '@ionic/react';
import { arrowBackOutline } from 'ionicons/icons';
import './GameScreenHeader.css';

interface GameScreenHeaderProps {
  eyebrow: string;
  title: string;
  onBack: () => void;
}

const GameScreenHeader: React.FC<GameScreenHeaderProps> = ({ eyebrow, title, onBack }) => (
  <header className="game-screen-header">
    <IonButton className="game-screen-header__back" fill="clear" onClick={onBack} aria-label="Back to main menu">
      <IonIcon icon={arrowBackOutline} slot="icon-only" />
    </IonButton>

    <div className="game-screen-header__copy">
      <p>{eyebrow}</p>
      <h1>{title}</h1>
    </div>

    <span className="game-screen-header__balance" aria-hidden="true" />
  </header>
);

export default GameScreenHeader;
