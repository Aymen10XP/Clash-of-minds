import { useId } from 'react';
import GameChoiceCard from './GameChoiceCard';
import GameSubpage from './GameSubpage';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import type { AppRoute } from '../../routing/routes';
import './ModeSelectionPage.css';

export interface ModeSelectionChoice {
  route: AppRoute;
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
  backRoute: AppRoute;
  choices: readonly ModeSelectionChoice[];
  className?: string;
}

const ModeSelectionPage: React.FC<ModeSelectionPageProps> = ({
  eyebrow,
  title,
  kicker,
  heading,
  description,
  backRoute,
  choices,
  className = '',
}) => {
  const titleId = useId();
  const { goBackAfterPress, navigateAfterPress, pendingRoute } = usePressNavigation();

  return (
    <GameSubpage
      eyebrow={eyebrow}
      title={title}
      onBack={() => goBackAfterPress(backRoute)}
      className={`mode-selection-page ${className}`.trim()}
    >
      <div className="mode-selection-content">
        <section className="mode-selection-intro" aria-labelledby={titleId}>
          <p className="mode-selection-intro__kicker">{kicker}</p>
          <h2 id={titleId}>{heading}</h2>
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
