import type { PropsWithChildren } from 'react';
import { IonContent, IonPage } from '@ionic/react';
import GameBackdrop from './GameBackdrop';
import './GamePage.css';

type GamePageProps = PropsWithChildren<{
  className?: string;
}>;

const GamePage: React.FC<GamePageProps> = ({ children, className = '' }) => (
  <IonPage>
    <IonContent fullscreen className={`game-page ${className}`.trim()}>
      <GameBackdrop />
      {children}
    </IonContent>
  </IonPage>
);

export default GamePage;
