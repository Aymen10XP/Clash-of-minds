import { type PropsWithChildren } from 'react';
import { IonSpinner } from '@ionic/react';
import { Navigate } from 'react-router-dom';
import GamePage from '../../components/game/GamePage';
import { appRoutes } from '../../routing/routes';
import { useAuth } from './context';
import './AuthGate.css';

const SessionLoading: React.FC = () => (
  <GamePage className="session-loading-page">
    <main className="session-loading" role="status" aria-label="Checking session">
      <IonSpinner name="crescent" />
      <span>Checking session</span>
    </main>
  </GamePage>
);

export const RequireAuth: React.FC<PropsWithChildren> = ({ children }) => {
  const { status } = useAuth();

  if (status === 'loading') return <SessionLoading />;
  if (status === 'anonymous') return <Navigate to={appRoutes.login} replace />;
  return children;
};

export const PublicOnly: React.FC<PropsWithChildren> = ({ children }) => {
  const { status } = useAuth();

  if (status === 'loading') return <SessionLoading />;
  if (status === 'authenticated') return <Navigate to={appRoutes.home} replace />;
  return children;
};
