import { useEffect, useRef, useState } from 'react';
import {
  IonButton,
  IonContent,
  IonIcon,
  IonPage,
  IonText,
} from '@ionic/react';
import { Haptics, ImpactStyle } from '@capacitor/haptics';
import { useNavigate } from 'react-router-dom';
import {
  bookOutline,
  chevronForwardOutline,
  gameControllerOutline,
  peopleOutline,
  settingsOutline,
  volumeHighOutline,
  volumeMuteOutline,
} from 'ionicons/icons';
import './Home.css';

const menuItems = [
  {
    label: 'Story Mode',
    description: 'Uncover the lost archives',
    icon: bookOutline,
    route: '/story',
    featured: true,
  },
  {
    label: 'VS Bot',
    description: 'Train against the machine',
    icon: gameControllerOutline,
    route: '/practice',
    featured: false,
  },
  {
    label: 'Multiplayer',
    description: 'Enter the online arena',
    icon: peopleOutline,
    route: '/multiplayer',
    featured: false,
  },
  {
    label: 'Settings',
    description: 'Tune your experience',
    icon: settingsOutline,
    route: '/settings',
    featured: false,
  },
] as const;

const particles = [
  { className: 'particle particle--one' },
  { className: 'particle particle--two' },
  { className: 'particle particle--three' },
  { className: 'particle particle--four' },
  { className: 'particle particle--five' },
] as const;

const romanNumerals = ['I', 'II', 'III', 'IV'] as const;

const playSelectionSound = () => {
  const LegacyAudioContext = (
    window as typeof window & { webkitAudioContext?: typeof AudioContext }
  ).webkitAudioContext;
  const AudioContextConstructor = window.AudioContext ?? LegacyAudioContext;

  if (!AudioContextConstructor) return;

  const context = new AudioContextConstructor();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  const now = context.currentTime;

  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(390, now);
  oscillator.frequency.exponentialRampToValueAtTime(760, now + 0.1);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.13, now + 0.012);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start(now);
  oscillator.stop(now + 0.17);
  oscillator.addEventListener('ended', () => void context.close(), { once: true });
};

const Home: React.FC = () => {
  const navigate = useNavigate();
  const themeAudioRef = useRef<HTMLAudioElement>(null);
  const navigationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isMusicPlaying, setIsMusicPlaying] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);

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
      if (navigationTimerRef.current) {
        clearTimeout(navigationTimerRef.current);
      }

      if (audio && !audio.paused) {
        audio.pause();
      }
    };
  }, []);

  const toggleThemeMusic = async () => {
    const audio = themeAudioRef.current;
    if (!audio) return;

    playSelectionSound();
    void Haptics.impact({ style: ImpactStyle.Light }).catch(() => undefined);

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

  const handleMenuSelect = (route: string) => {
    if (selectedRoute) return;

    setSelectedRoute(route);
    playSelectionSound();
    void Haptics.impact({ style: ImpactStyle.Medium }).catch(() => undefined);

    navigationTimerRef.current = setTimeout(() => {
      navigate(route);
    }, 620);
  };

  return (
    <IonPage>
      <IonContent fullscreen className="menu-page">
        <div className="ambient-field" aria-hidden="true">
          {particles.map((particle) => (
            <span key={particle.className} className={particle.className} />
          ))}
          <span className="archive-ring archive-ring--outer" />
          <span className="archive-ring archive-ring--inner" />
          <span className="civilization-frieze civilization-frieze--top" />
          <span className="civilization-frieze civilization-frieze--bottom" />
        </div>

        <audio
          ref={themeAudioRef}
          src="/media/music/forensic-theories.wav"
          preload="auto"
          autoPlay
          loop
        />

        <main className="menu-shell">
          <header className="menu-header">
            <div className="archive-status">
              <span className="archive-status__line" aria-hidden="true" />
              Archive link established
            </div>
            <IonButton
              className="sound-control"
              fill="clear"
              onClick={toggleThemeMusic}
              aria-label={isMusicPlaying ? 'Pause theme music' : 'Play theme music'}
            >
              <IonIcon icon={isMusicPlaying ? volumeHighOutline : volumeMuteOutline} />
            </IonButton>
          </header>

          <section className="brand-block" aria-labelledby="game-title">
            <div className="brand-seal" aria-hidden="true">
              <span className="brand-seal__century">XXI</span>
              <span className="brand-seal__monogram">CM</span>
            </div>

            <div className="brand-copy">
              <IonText color="light">
                <p className="brand-kicker">Past meets protocol</p>
                <h1 id="game-title">
                  Clash of <strong>Minds</strong>
                </h1>
              </IonText>
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

          <p className="menu-footer">
            <span aria-hidden="true" />
            Select a chronicle
            <span aria-hidden="true" />
          </p>
        </main>
      </IonContent>
    </IonPage>
  );
};

export default Home;
