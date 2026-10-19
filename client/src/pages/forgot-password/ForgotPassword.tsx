import { mailOutline } from 'ionicons/icons';
import { useNavigate } from 'react-router-dom';
import AuthInput from '../../components/auth/AuthInput';
import AuthPage from '../../components/auth/AuthPage';
import { requestPasswordReset } from '../../features/auth/api';
import { appRoutes } from '../../routing/routes';
import './ForgotPassword.css';

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();

  const handleSubmit = async (formData: FormData) => {
    const response = await requestPasswordReset(String(formData.get('email') ?? ''));

    if (response.debugResetUrl) {
      const resetPath = new URL(response.debugResetUrl, window.location.origin).pathname;
      navigate(resetPath, {
        replace: true,
        state: { notice: 'Development mode: your secure reset link is ready.' },
      });
      return;
    }

    navigate(appRoutes.login, { replace: true, state: { notice: response.message } });
  };

  return (
    <AuthPage
      className="forgot-password-page"
      formLabel="Forgot password"
      submitLabel="Send reset link"
      alternatePrompt="Remembered your password?"
      alternateLabel="Sign in"
      alternateRoute={appRoutes.login}
      backRoute={appRoutes.login}
      onSubmit={handleSubmit}
    >
      <p className="password-reset-intro">
        Enter the email linked to your account. We will send you a secure, one-hour reset link.
      </p>
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
    </AuthPage>
  );
};

export default ForgotPassword;
