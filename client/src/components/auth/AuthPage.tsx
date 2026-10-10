import { Children, useState, type FormEvent, type PropsWithChildren } from 'react';
import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCol,
  IonGrid,
  IonIcon,
  IonRow,
} from '@ionic/react';
import { arrowBackOutline } from 'ionicons/icons';
import GamePage from '../game/GamePage';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import { playUiFeedback } from '../../lib/uiFeedback';
import type { AppRoute } from '../../routing/routes';
import './AuthPage.css';

type AuthPageProps = PropsWithChildren<{
  className: string;
  formLabel: string;
  submitLabel: string;
  alternatePrompt: string;
  alternateLabel: string;
  alternateRoute: AppRoute;
  backRoute: AppRoute;
}>;

const AuthPage: React.FC<AuthPageProps> = ({
  children,
  className,
  formLabel,
  submitLabel,
  alternatePrompt,
  alternateLabel,
  alternateRoute,
  backRoute,
}) => {
  const [previewNotice, setPreviewNotice] = useState('');
  const { goBackAfterPress, navigateAfterPress, pendingRoute } = usePressNavigation({
    delay: 160,
    feedback: 'light',
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    playUiFeedback('medium');
    setPreviewNotice('The screen is ready. Account connection comes in the next backend step.');
  };

  return (
    <GamePage className={`auth-page ${className}`}>
      <IonGrid fixed className="auth-shell" role="main">
        <IonRow className="auth-topbar ion-align-items-center">
          <IonCol className="auth-topbar__side ion-no-padding" size="auto">
            <IonButton
              className="auth-back"
              fill="clear"
              onClick={() => goBackAfterPress(backRoute)}
              aria-label="Go back"
            >
              <IonIcon icon={arrowBackOutline} slot="icon-only" />
            </IonButton>
          </IonCol>

          <IonCol className="auth-topbar__brand ion-no-padding">
            <img
              className="auth-wordmark"
              src="/media/images/logo/clash-of-minds-logo.png"
              alt="Clash of Minds"
            />
          </IonCol>

          <IonCol
            className="auth-topbar__side ion-no-padding"
            size="auto"
            aria-hidden="true"
          >
            <span className="auth-topbar__balance" />
          </IonCol>
        </IonRow>

        <IonRow className="auth-layout ion-align-items-center ion-justify-content-center">
          <IonCol className="auth-layout__column ion-no-padding" size="12">
            <IonCard
              className="auth-panel"
              role="region"
              aria-label={`${formLabel} form`}
            >
              <IonCardContent className="auth-panel__content">
                <form className="auth-form" onSubmit={handleSubmit}>
                  <IonGrid className="auth-fields ion-no-padding">
                    {Children.map(children, (child) => (
                      <IonRow className="auth-field-row">
                        <IonCol className="ion-no-padding">{child}</IonCol>
                      </IonRow>
                    ))}
                  </IonGrid>

                  <IonButton className="auth-submit" expand="block" type="submit">
                    {submitLabel}
                  </IonButton>

                  {previewNotice && (
                    <p className="auth-preview-notice" role="status">
                      {previewNotice}
                    </p>
                  )}

                  <IonRow className="auth-alternate ion-align-items-center ion-justify-content-center">
                    <span>{alternatePrompt}</span>
                    <IonButton
                      className="auth-alternate__button"
                      fill="clear"
                      type="button"
                      disabled={Boolean(pendingRoute)}
                      onClick={() => navigateAfterPress(alternateRoute)}
                    >
                      {alternateLabel}
                    </IonButton>
                  </IonRow>
                </form>
              </IonCardContent>
            </IonCard>
          </IonCol>
        </IonRow>
      </IonGrid>
    </GamePage>
  );
};

export default AuthPage;
