import { lockClosedOutline } from 'ionicons/icons';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import AuthInput from '../../components/auth/AuthInput';
import AuthPage from '../../components/auth/AuthPage';
import { confirmPasswordReset } from '../../features/auth/api';
import { appRoutes } from '../../routing/routes';
import './ResetPassword.css';

type ResetLocationState = { notice?: string } | null;

const ResetPassword: React.FC = () => {
  const { uid = '', token = '' } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const notice = (location.state as ResetLocationState)?.notice;

  const handleSubmit = async (formData: FormData) => {
    const response = await confirmPasswordReset({
      uid,
      token,
      password: String(formData.get('password') ?? ''),
      confirmPassword: String(formData.get('confirmPassword') ?? ''),
    });
    navigate(appRoutes.login, { replace: true, state: { notice: response.message } });
  };

  return (
    <AuthPage
      className="reset-password-page"
      formLabel="Choose a new password"
      submitLabel="Reset password"
      alternatePrompt="Return to your account"
      alternateLabel="Sign in"
      alternateRoute={appRoutes.login}
      backRoute={appRoutes.login}
      notice={notice}
      onSubmit={handleSubmit}
    >
      <AuthInput
        icon={lockClosedOutline}
        name="password"
        label="New password"
        placeholder="Enter a new password"
        type="password"
        autocomplete="new-password"
        minlength={8}
        passwordToggle
        required
      />
      <AuthInput
        icon={lockClosedOutline}
        name="confirmPassword"
        label="Confirm new password"
        placeholder="Repeat your new password"
        type="password"
        autocomplete="new-password"
        minlength={8}
        passwordToggle
        required
      />
    </AuthPage>
  );
};

export default ResetPassword;
