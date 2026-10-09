import { useCallback, useEffect, useRef, useState } from 'react';
import { useIonRouter, useIonViewWillEnter, useIonViewWillLeave } from '@ionic/react';
import { playUiFeedback, type FeedbackIntensity } from '../lib/uiFeedback';
import type { AppRoute } from '../routing/routes';

interface PressNavigationOptions {
  delay?: number;
  feedback?: FeedbackIntensity;
}

export const usePressNavigation = ({
  delay = 220,
  feedback = 'medium',
}: PressNavigationOptions = {}) => {
  const { canGoBack, goBack, push } = useIonRouter();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingRouteRef = useRef<AppRoute | null>(null);
  const [pendingRoute, setPendingRoute] = useState<AppRoute | null>(null);

  const cancelScheduledNavigation = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    pendingRouteRef.current = null;
  }, []);

  const reset = useCallback(() => {
    cancelScheduledNavigation();
    setPendingRoute(null);
  }, [cancelScheduledNavigation]);

  useIonViewWillEnter(reset);
  useIonViewWillLeave(cancelScheduledNavigation);
  useEffect(() => () => cancelScheduledNavigation(), [cancelScheduledNavigation]);

  const scheduleNavigation = useCallback(
    (route: AppRoute, direction: 'forward' | 'back', intensity: FeedbackIntensity) => {
      if (pendingRouteRef.current) return;

      pendingRouteRef.current = route;
      setPendingRoute(route);
      playUiFeedback(intensity);

      timerRef.current = setTimeout(() => {
        timerRef.current = null;

        if (direction === 'back') {
          if (canGoBack()) {
            goBack();
          } else {
            push(route, 'back', 'replace');
          }

          return;
        }

        push(route, 'forward', 'push');
      }, delay);
    },
    [canGoBack, delay, goBack, push],
  );

  const navigateAfterPress = useCallback(
    (route: AppRoute, intensity: FeedbackIntensity = feedback) => {
      scheduleNavigation(route, 'forward', intensity);
    },
    [feedback, scheduleNavigation],
  );

  const goBackAfterPress = useCallback(
    (fallbackRoute: AppRoute, intensity: FeedbackIntensity = 'light') => {
      scheduleNavigation(fallbackRoute, 'back', intensity);
    },
    [scheduleNavigation],
  );

  return { goBackAfterPress, navigateAfterPress, pendingRoute };
};
