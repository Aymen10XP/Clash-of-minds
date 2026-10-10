import { useEffect, useRef, useState } from 'react';
import { IonButton, IonCol, IonGrid, IonIcon, IonRow } from '@ionic/react';
import {
  bookOutline,
  chevronForwardOutline,
  gameControllerOutline,
  logOutOutline,
  peopleOutline,
  settingsOutline,
  volumeHighOutline,
  volumeMuteOutline,
} from 'ionicons/icons';
import GamePage from '../../components/game/GamePage';
import { useAuth } from '../../features/auth/context';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import { playUiFeedback } from '../../lib/uiFeedback';
import { appRoutes, type AppRoute } from '../../routing/routes';
import './Home.css';

const menuItems = [
  {
    label: 'Story Mode',
    description: 'Uncover the lost archives',
    icon: bookOutline,
    route: appRoutes.story,
  },
  {
    label: 'VS Bot',
    description: 'Train against the machine',
    icon: gameControllerOutline,
    route: appRoutes.practice,
  },
  {
    label: 'Multiplayer',
    description: 'Enter the online arena',
    icon: peopleOutline,
    route: appRoutes.multiplayer,
  },
  {
    label: 'Settings',
    description: 'Tune your experience',
    icon: settingsOutline,
    route: appRoutes.settings,
  },
] as const;

const romanNumerals = ['I', 'II', 'III', 'IV'] as const;

const Home: React.FC = () => {
  const themeAudioRef = useRef<HTMLAudioElement>(null);
  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const { logout, user } = useAuth();
  const { navigateAfterPress, pendingRoute: selectedRoute } = usePressNavigation({ delay: 320 });

  useEffect(() => {
    const audio = themeAudioRef.current;

    if (audio) {
      audio.volume = 0.32;
      void audio
        .play()
        .then(() => setIsMusicPlaying(true))
        .catch(() => setIsMusicPlaying(false));
    }

    return () => {
      if (audio && !audio.paused) {
        audio.pause();
      }
    };
  }, []);

  const toggleThemeMusic = async () => {
    const audio = themeAudioRef.current;
    if (!audio) return;

    playUiFeedback('light');

    if (audio.paused) {
      audio.volume = 0.32;

      try {
        await audio.play();
        setIsMusicPlaying(true);
      } catch {
        setIsMusicPlaying(false);
      }
    } else {
      audio.pause();
      setIsMusicPlaying(false);
    }
  };

  const handleMenuSelect = (route: AppRoute) => {
    navigateAfterPress(route);
  };

  const handleLogout = async () => {
    playUiFeedback('light');
    setIsLoggingOut(true);

    try {
      await logout();
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <GamePage className="menu-page">
      <audio
        ref={themeAudioRef}
        src="/media/music/forensic-theories.wav"
        preload="auto"
        autoPlay
        loop
      />

      <IonGrid
        fixed
        className="menu-shell ion-display-flex ion-flex-column ion-justify-content-center"
        role="main"
      >
        <IonRow className="menu-header ion-align-items-center ion-justify-content-end">
          <IonCol className="ion-no-padding" size="auto">
            <IonButton
              className="account-control"
              fill="clear"
              disabled={isLoggingOut}
              onClick={() => void handleLogout()}
              aria-label={`Log out${user ? ` ${user.username}` : ''}`}
            >
              <IonIcon icon={logOutOutline} />
            </IonButton>
          </IonCol>
          <IonCol className="ion-no-padding" size="auto">
            <IonButton
              className="sound-control"
              fill="clear"
              onClick={toggleThemeMusic}
              aria-label={isMusicPlaying ? 'Pause theme music' : 'Play theme music'}
            >
              <IonIcon icon={isMusicPlaying ? volumeHighOutline : volumeMuteOutline} />
            </IonButton>
          </IonCol>
        </IonRow>

        <IonRow className="brand-block ion-justify-content-center">
          <IonCol className="ion-no-padding" size="auto">
            <div className="logo-gloss">
              <img
                className="game-logo"
                src="/media/images/logo/clash-of-minds-logo.png"
                alt="Clash of Minds"
              />
            </div>
          </IonCol>
        </IonRow>

        <IonRow className="game-menu" role="navigation" aria-label="Game modes">
          {menuItems.map((item, index) => (
            <IonCol
              className="game-menu__column ion-display-flex"
              key={item.route}
              size="12"
              sizeMd="6"
            >
              <IonButton
                className={`menu-button${
                  selectedRoute === item.route ? ' menu-button--selected' : ''
                }${selectedRoute && selectedRoute !== item.route ? ' menu-button--receding' : ''}`}
                expand="block"
                fill="clear"
                disabled={Boolean(selectedRoute && selectedRoute !== item.route)}
                onClick={() => handleMenuSelect(item.route)}
                aria-label={`${item.label}: ${item.description}`}
                style={{ '--menu-order': index } as React.CSSProperties}
              >
                <span className="menu-button__number" aria-hidden="true">
                  {romanNumerals[index]}
                </span>
                <span className="menu-button__flare" aria-hidden="true" />
                <span className="menu-button__icon" aria-hidden="true">
                  <IonIcon icon={item.icon} />
                </span>
                <span className="menu-button__copy">
                  <span className="menu-button__label">{item.label}</span>
                  <span className="menu-button__description">{item.description}</span>
                </span>
                <IonIcon
                  className="menu-button__arrow"
                  icon={chevronForwardOutline}
                  aria-hidden="true"
                />
              </IonButton>
            </IonCol>
          ))}
        </IonRow>
      </IonGrid>
    </GamePage>
  );
};

export default Home;
