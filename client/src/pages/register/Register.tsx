import {
  lockClosedOutline,
  mailOutline,
  personOutline,
} from 'ionicons/icons';
import { useNavigate } from 'react-router-dom';
import AuthInput from '../../components/auth/AuthInput';
import AuthPage from '../../components/auth/AuthPage';
import CountryCombobox from '../../components/auth/CountryCombobox';
import { useAuth } from '../../features/auth/context';
import { appRoutes } from '../../routing/routes';
import './Register.css';

const Register: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (formData: FormData) => {
    await register({
      username: String(formData.get('username') ?? ''),
      email: String(formData.get('email') ?? ''),
      country: String(formData.get('country') ?? ''),
      password: String(formData.get('password') ?? ''),
      confirmPassword: String(formData.get('confirmPassword') ?? ''),
    });
    navigate(appRoutes.login, {
      replace: true,
      state: { notice: 'Account created. Sign in to continue.' },
    });
  };

  return (
    <AuthPage
      className="register-page"
      formLabel="Create account"
      submitLabel="Create account"
      alternatePrompt="Already registered?"
      alternateLabel="Sign in"
      alternateRoute={appRoutes.login}
      backRoute={appRoutes.home}
      onSubmit={handleSubmit}
    >
    <AuthInput
      icon={personOutline}
      name="username"
      label="Username"
      placeholder="Choose a username"
      autocomplete="username"
      minlength={3}
      required
    />

    <AuthInput
      icon={mailOutline}
      name="email"
      label="Email"
      placeholder="you@example.com"
      type="email"
      autocomplete="email"
      inputmode="email"
      required
    />

    <CountryCombobox />

    <AuthInput
      icon={lockClosedOutline}
      name="password"
      label="Password"
      placeholder="Create a password"
      type="password"
      autocomplete="new-password"
      minlength={8}
      passwordToggle
      required
    />

    <AuthInput
      icon={lockClosedOutline}
      name="confirmPassword"
      label="Confirm password"
      placeholder="Repeat your password"
      type="password"
      autocomplete="new-password"
      minlength={8}
      passwordToggle
      required
    />
    </AuthPage>
  );
};

export default Register;
