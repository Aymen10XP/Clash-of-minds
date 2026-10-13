import { Haptics, ImpactStyle } from '@capacitor/haptics';

export type FeedbackIntensity = 'light' | 'medium' | 'heavy';

const impactStyles: Record<FeedbackIntensity, ImpactStyle> = {
  light: ImpactStyle.Light,
  medium: ImpactStyle.Medium,
  heavy: ImpactStyle.Heavy,
};

export const playUiFeedback = (intensity: FeedbackIntensity = 'medium') => {
  void Haptics.impact({ style: impactStyles[intensity] }).catch(() => undefined);
};
