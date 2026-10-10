import type { PropsWithChildren } from 'react';
import { IonContent, IonGrid, IonPage } from '@ionic/react';
import GameBackdrop from './GameBackdrop';
import './GamePage.css';

type GamePageProps = PropsWithChildren<{
  className?: string;
}>;

const GamePage: React.FC<GamePageProps> = ({ children, className = '' }) => (
  <IonPage>
    <IonContent fullscreen className={`game-page ${className}`.trim()}>
      <GameBackdrop />
      <IonGrid className="game-page__content ion-no-padding">{children}</IonGrid>
    </IonContent>
  </IonPage>
);

export default GamePage;
