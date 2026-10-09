import { useState, type FormEvent, type PropsWithChildren } from 'react';
import { IonButton, IonIcon } from '@ionic/react';
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
      <main className="auth-shell">
        <header className="auth-topbar">
          <IonButton
            className="auth-back"
            fill="clear"
            onClick={() => goBackAfterPress(backRoute)}
            aria-label="Go back"
          >
            <IonIcon icon={arrowBackOutline} slot="icon-only" />
          </IonButton>

          <img
            className="auth-wordmark"
            src="/media/images/logo/clash-of-minds-logo.png"
            alt="Clash of Minds"
          />

          <span className="auth-topbar__balance" aria-hidden="true" />
        </header>

        <div className="auth-layout">
          <section className="auth-panel" aria-label={`${formLabel} form`}>
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="auth-fields">{children}</div>

              <IonButton className="auth-submit" expand="block" type="submit">
                {submitLabel}
              </IonButton>

              {previewNotice && (
                <p className="auth-preview-notice" role="status">
                  {previewNotice}
                </p>
              )}

              <div className="auth-alternate">
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
              </div>
            </form>
          </section>
        </div>
      </main>
    </GamePage>
  );
};

export default AuthPage;
