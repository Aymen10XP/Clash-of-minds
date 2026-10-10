import { IonCheckbox, IonRow } from '@ionic/react';
import { lockClosedOutline, personOutline } from 'ionicons/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import AuthInput from '../../components/auth/AuthInput';
import AuthPage from '../../components/auth/AuthPage';
import { useAuth } from '../../features/auth/context';
import { appRoutes } from '../../routing/routes';
import './Login.css';

type LoginLocationState = { notice?: string } | null;

const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const notice = (location.state as LoginLocationState)?.notice;

  const handleSubmit = async (formData: FormData) => {
    await login({
      identity: String(formData.get('identity') ?? ''),
      password: String(formData.get('password') ?? ''),
      rememberMe: formData.has('rememberMe'),
    });
    navigate(appRoutes.home, { replace: true });
  };

  return (
    <AuthPage
      className="login-page"
      formLabel="Login"
      submitLabel="Sign in"
      alternatePrompt="New challenger?"
      alternateLabel="Create an account"
      alternateRoute={appRoutes.register}
      backRoute={appRoutes.home}
      notice={notice}
      onSubmit={handleSubmit}
    >
      <AuthInput
        icon={personOutline}
        name="identity"
        label="Username or email"
        placeholder="Enter your username or email"
        autocomplete="username"
        inputmode="email"
        required
      />

      <AuthInput
        icon={lockClosedOutline}
        name="password"
        label="Password"
        placeholder="Enter your password"
        type="password"
        autocomplete="current-password"
        passwordToggle
        required
      />

      <IonRow className="auth-form-options ion-align-items-center ion-justify-content-between">
        <IonCheckbox className="auth-checkbox" name="rememberMe" labelPlacement="end">
          Keep me signed in
        </IonCheckbox>
      </IonRow>
    </AuthPage>
  );
};

export default Login;
