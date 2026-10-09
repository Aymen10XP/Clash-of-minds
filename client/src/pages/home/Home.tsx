import { useEffect, useRef, useState } from 'react';
import { IonButton, IonIcon } from '@ionic/react';
import {
  bookOutline,
  chevronForwardOutline,
  gameControllerOutline,
  peopleOutline,
  settingsOutline,
  volumeHighOutline,
  volumeMuteOutline,
} from 'ionicons/icons';
import GamePage from '../../components/game/GamePage';
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
    featured: true,
  },
  {
    label: 'VS Bot',
    description: 'Train against the machine',
    icon: gameControllerOutline,
    route: appRoutes.practice,
    featured: false,
  },
  {
    label: 'Multiplayer',
    description: 'Enter the online arena',
    icon: peopleOutline,
    route: appRoutes.multiplayer,
    featured: false,
  },
  {
    label: 'Settings',
    description: 'Tune your experience',
    icon: settingsOutline,
    route: appRoutes.settings,
    featured: false,
  },
] as const;

const romanNumerals = ['I', 'II', 'III', 'IV'] as const;

const Home: React.FC = () => {
  const themeAudioRef = useRef<HTMLAudioElement>(null);
  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
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

  return (
    <GamePage className="menu-page">
        <audio
          ref={themeAudioRef}
          src="/media/music/forensic-theories.wav"
          preload="auto"
          autoPlay
          loop
        />

        <main className="menu-shell">
          <header className="menu-header">
            <IonButton
              className="sound-control"
              fill="clear"
              onClick={toggleThemeMusic}
              aria-label={isMusicPlaying ? 'Pause theme music' : 'Play theme music'}
            >
              <IonIcon icon={isMusicPlaying ? volumeHighOutline : volumeMuteOutline} />
            </IonButton>
          </header>

          <section className="brand-block">
            <div className="logo-gloss">
              <img
                className="game-logo"
                src="/media/images/logo/clash-of-minds-logo.png"
                alt="Clash of Minds"
              />
            </div>
          </section>

          <nav className="game-menu" aria-label="Game modes">
            {menuItems.map((item, index) => (
              <IonButton
                key={item.route}
                className={`menu-button${item.featured ? ' menu-button--featured' : ''}${
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
            ))}
          </nav>
        </main>
    </GamePage>
  );
};

export default Home;
