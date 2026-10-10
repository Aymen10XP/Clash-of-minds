import { IonCheckbox, IonRow } from '@ionic/react';
import { lockClosedOutline, personOutline } from 'ionicons/icons';
import AuthInput from '../../components/auth/AuthInput';
import AuthPage from '../../components/auth/AuthPage';
import { appRoutes } from '../../routing/routes';
import './Login.css';

const Login: React.FC = () => (
  <AuthPage
    className="login-page"
    formLabel="Login"
    submitLabel="Sign in"
    alternatePrompt="New challenger?"
    alternateLabel="Create an account"
    alternateRoute={appRoutes.register}
    backRoute={appRoutes.home}
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

export default Login;
