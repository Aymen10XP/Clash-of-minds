import { useState } from 'react';
import { IonBadge, IonCol, IonGrid, IonNote, IonRow } from '@ionic/react';
import GameChoiceCard from '../../../components/game/GameChoiceCard';
import GameSubpage from '../../../components/game/GameSubpage';
import { practiceTopics } from '../../../features/practice/topics';
import { usePressNavigation } from '../../../hooks/usePressNavigation';
import { playUiFeedback } from '../../../lib/uiFeedback';
import { appRoutes } from '../../../routing/routes';
import './PracticeTopics.css';

const PracticeTopics: React.FC = () => {
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
  const selectedTopic = practiceTopics.find((topic) => topic.id === selectedTopicId);

  const handleBack = () => {
    goBackAfterPress(appRoutes.practice);
  };

  const handleTopicSelect = (topicId: string) => {
    playUiFeedback('light');
    setSelectedTopicId(topicId);
  };

  return (
    <GameSubpage
      eyebrow="Focused practice"
      title="Topic Catalogue"
      onBack={handleBack}
      className="practice-topics-page"
    >
      <IonGrid
        fixed
        className="topic-catalogue ion-no-padding"
        role="region"
        aria-labelledby="topic-title"
      >

        <IonRow className="topic-grid">
          {practiceTopics.map((topic) => (
            <IonCol
              className="topic-grid__column ion-display-flex"
              key={topic.id}
              size="12"
              sizeMd="6"
              sizeLg="4"
            >
              <GameChoiceCard
                compact
                title={topic.title}
                description={topic.description}
                meta={topic.era}
                icon={topic.icon}
                selected={selectedTopicId === topic.id}
                onSelect={() => handleTopicSelect(topic.id)}
              />
            </IonCol>
          ))}
        </IonRow>
      </IonGrid>
    </GameSubpage>
  );
};

export default PracticeTopics;
