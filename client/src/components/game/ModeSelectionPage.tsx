import { IonCol, IonGrid, IonRow } from '@ionic/react';
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
  backRoute: AppRoute;
  choices: readonly ModeSelectionChoice[];
  className?: string;
}

const ModeSelectionPage: React.FC<ModeSelectionPageProps> = ({
  eyebrow,
  title,
  backRoute,
  choices,
  className = '',
}) => {
  const { goBackAfterPress, navigateAfterPress, pendingRoute } = usePressNavigation();

  return (
    <GameSubpage
      eyebrow={eyebrow}
      title={title}
      onBack={() => goBackAfterPress(backRoute)}
      className={`mode-selection-page ${className}`.trim()}
    >
      <IonGrid fixed className="mode-selection-content ion-no-padding">
        <IonRow
          className="mode-selection-grid ion-justify-content-center"
          role="group"
          aria-label={`${title} modes`}
        >
          {choices.map((choice) => (
            <IonCol
              className="mode-selection-grid__column ion-display-flex ion-justify-content-center"
              key={choice.route}
              size="12"
              sizeMd="6"
            >
              <GameChoiceCard
                title={choice.title}
                description={choice.description}
                meta={choice.meta}
                icon={choice.icon}
                selected={pendingRoute === choice.route}
                disabled={Boolean(pendingRoute && pendingRoute !== choice.route)}
                onSelect={() => navigateAfterPress(choice.route)}
              />
            </IonCol>
          ))}
        </IonRow>
      </IonGrid>
    </GameSubpage>
  );
};

export default ModeSelectionPage;
