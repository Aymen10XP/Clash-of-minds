import { libraryOutline, trophyOutline } from 'ionicons/icons';
import GameChoiceCard from '../components/game/GameChoiceCard';
import GameSubpage from '../components/game/GameSubpage';
import { usePressNavigation } from '../hooks/usePressNavigation';
import { appRoutes } from '../routing/routes';
import './VsBot.css';

const VsBot: React.FC = () => {
  const { navigateAfterPress, pendingRoute } = usePressNavigation();

  const handleBack = () => {
    navigateAfterPress(appRoutes.home, 'light');
  };

  return (
    <GameSubpage
      eyebrow="Solo training"
      title="VS Bot"
      onBack={handleBack}
      className={`practice-page${pendingRoute ? ' practice-page--leaving' : ''}`}
    >
      <div className="practice-content">
        <section className="practice-intro" aria-labelledby="practice-title">
          <p className="practice-intro__kicker">Choose your trial</p>
          <h2 id="practice-title">How will you challenge the archive?</h2>
          <p>Climb until your first mistake, or master one field at a time.</p>
        </section>

        <section className="practice-modes" aria-label="Practice modes">
          <GameChoiceCard
            title="Top Score"
            description="Answer without limits. One wrong answer ends the run."
            meta="Endless ladder"
            icon={trophyOutline}
            selected={pendingRoute === appRoutes.practiceTopScore}
            disabled={Boolean(pendingRoute && pendingRoute !== appRoutes.practiceTopScore)}
            onSelect={() => navigateAfterPress(appRoutes.practiceTopScore)}
          />

          <GameChoiceCard
            title="Choose by Topic"
            description="Open the catalogue and train inside a chosen field."
            meta="Focused practice"
            icon={libraryOutline}
            selected={pendingRoute === appRoutes.practiceTopics}
            disabled={Boolean(pendingRoute && pendingRoute !== appRoutes.practiceTopics)}
            onSelect={() => navigateAfterPress(appRoutes.practiceTopics)}
          />
        </section>
      </div>
    </GameSubpage>
  );
};

export default VsBot;
