import { useCallback, useEffect, useRef, useState } from 'react';
import { useIonViewWillEnter } from '@ionic/react';
import { useNavigate } from 'react-router-dom';
import { playUiFeedback, type FeedbackIntensity } from '../lib/uiFeedback';

interface PressNavigationOptions {
  delay?: number;
  feedback?: FeedbackIntensity;
}

export const usePressNavigation = ({
  delay = 360,
  feedback = 'medium',
}: PressNavigationOptions = {}) => {
  const navigate = useNavigate();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [pendingRoute, setPendingRoute] = useState<string | null>(null);

  const reset = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    setPendingRoute(null);
  }, []);

  useIonViewWillEnter(reset);
  useEffect(() => reset, [reset]);

  const navigateAfterPress = (route: string, intensity = feedback) => {
    if (pendingRoute) return;

    setPendingRoute(route);
    playUiFeedback(intensity);
    timerRef.current = setTimeout(() => navigate(route), delay);
  };

  return { navigateAfterPress, pendingRoute };
};
