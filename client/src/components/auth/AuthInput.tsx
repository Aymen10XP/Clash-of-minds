import type { ComponentProps } from 'react';
import { IonIcon, IonInput, IonInputPasswordToggle } from '@ionic/react';

type IonicInputProps = ComponentProps<typeof IonInput>;

interface AuthInputProps extends Omit<IonicInputProps, 'className' | 'fill' | 'labelPlacement'> {
  icon: string;
  passwordToggle?: boolean;
}

const AuthInput: React.FC<AuthInputProps> = ({ icon, passwordToggle = false, ...inputProps }) => (
  <IonInput className="auth-input" fill="outline" labelPlacement="stacked" {...inputProps}>
    <IonIcon icon={icon} slot="start" aria-hidden="true" />
    {passwordToggle && <IonInputPasswordToggle slot="end" color="warning" />}
  </IonInput>
);

export default AuthInput;
