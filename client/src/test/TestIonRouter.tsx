import { useMemo, type PropsWithChildren } from 'react';
import { IonApp, IonRouterContext } from '@ionic/react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';

type TestIonRouterProps = PropsWithChildren<{
  initialEntry: string;
}>;

const IonicRouterBridge: React.FC<PropsWithChildren> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const router = useMemo<React.ContextType<typeof IonRouterContext>>(
    () => ({
      routeInfo: {
        id: location.key,
        pathname: location.pathname,
        search: location.search,
      },
      push: (pathname, _direction, action) => {
        navigate(pathname, { replace: action === 'replace' });
      },
      back: () => navigate(-1),
      navigateRoot: (pathname) => navigate(pathname, { replace: true }),
      canGoBack: () => location.key !== 'default',
      nativeBack: () => navigate(-1),
    }),
    [location.key, location.pathname, location.search, navigate],
  );

  return <IonRouterContext.Provider value={router}>{children}</IonRouterContext.Provider>;
};

const TestIonRouter: React.FC<TestIonRouterProps> = ({ initialEntry, children }) => (
  <IonApp>
    <MemoryRouter initialEntries={[initialEntry]}>
      <IonicRouterBridge>{children}</IonicRouterBridge>
    </MemoryRouter>
  </IonApp>
);

export default TestIonRouter;
