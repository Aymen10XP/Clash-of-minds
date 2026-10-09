import GameChoiceCard from './GameChoiceCard';
import GameSubpage from './GameSubpage';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import './ModeSelectionPage.css';

export interface ModeSelectionChoice {
  route: string;
  title: string;
  description: string;
  meta: string;
  icon: string;
}

interface ModeSelectionPageProps {
  eyebrow: string;
  title: string;
  kicker: string;
  heading: string;
  description: string;
  backRoute: string;
  choices: readonly ModeSelectionChoice[];
}

const ModeSelectionPage: React.FC<ModeSelectionPageProps> = ({
  eyebrow,
  title,
  kicker,
  heading,
  description,
  backRoute,
  choices,
}) => {
  const { navigateAfterPress, pendingRoute } = usePressNavigation();

  return (
    <GameSubpage
      eyebrow={eyebrow}
      title={title}
      onBack={() => navigateAfterPress(backRoute, 'light')}
      className={`mode-selection-page${pendingRoute ? ' mode-selection-page--leaving' : ''}`}
    >
      <div className="mode-selection-content">
        <section className="mode-selection-intro" aria-labelledby="mode-selection-title">
          <p className="mode-selection-intro__kicker">{kicker}</p>
          <h2 id="mode-selection-title">{heading}</h2>
          <p>{description}</p>
        </section>

        <section className="mode-selection-grid" aria-label={`${title} modes`}>
          {choices.map((choice) => (
            <GameChoiceCard
              key={choice.route}
              title={choice.title}
              description={choice.description}
              meta={choice.meta}
              icon={choice.icon}
              selected={pendingRoute === choice.route}
              disabled={Boolean(pendingRoute && pendingRoute !== choice.route)}
              onSelect={() => navigateAfterPress(choice.route)}
            />
          ))}
        </section>
      </div>
    </GameSubpage>
  );
};

export default ModeSelectionPage;
