import { IonButton, IonCol, IonIcon, IonRow } from '@ionic/react';
import { arrowBackOutline } from 'ionicons/icons';
import './GameScreenHeader.css';

interface GameScreenHeaderProps {
  eyebrow: string;
  title: string;
  onBack: () => void;
  backLabel?: string;
}

const GameScreenHeader: React.FC<GameScreenHeaderProps> = ({
  eyebrow,
  title,
  onBack,
  backLabel = 'Go back',
}) => (
  <IonRow className="game-screen-header ion-align-items-center">
    <IonCol className="game-screen-header__side ion-no-padding" size="auto">
      <IonButton
        className="game-screen-header__back"
        fill="clear"
        onClick={onBack}
        aria-label={backLabel}
      >
        <IonIcon icon={arrowBackOutline} slot="icon-only" />
      </IonButton>
    </IonCol>

    <IonCol className="game-screen-header__copy ion-no-padding">
      <p>{eyebrow}</p>
      <h1>{title}</h1>
    </IonCol>

    <IonCol className="game-screen-header__side ion-no-padding" size="auto" aria-hidden="true">
      <span className="game-screen-header__balance" />
    </IonCol>
  </IonRow>
);

export default GameScreenHeader;
