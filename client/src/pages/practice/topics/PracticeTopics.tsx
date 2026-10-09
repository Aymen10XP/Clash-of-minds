import { useState } from 'react';
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
      <section className="topic-catalogue" aria-labelledby="topic-title">
        <div className="topic-catalogue__heading">
          <div>
            <p>Knowledge catalogue</p>
            <h2 id="topic-title">Select a topic</h2>
          </div>
          <span>{practiceTopics.length} archives</span>
        </div>

        <p className="topic-catalogue__intro">
          Focus your training on one archive. Your selected topic will define the next challenge.
        </p>

        <div className="topic-grid">
          {practiceTopics.map((topic) => (
            <GameChoiceCard
              key={topic.id}
              compact
              title={topic.title}
              description={topic.description}
              meta={topic.era}
              icon={topic.icon}
              selected={selectedTopicId === topic.id}
              onSelect={() => handleTopicSelect(topic.id)}
            />
          ))}
        </div>

        <p className="topic-catalogue__selection" aria-live="polite">
          {selectedTopic
            ? `${selectedTopic.title} selected. Your training path is ready.`
            : 'Choose one archive to prepare your training path.'}
        </p>
      </section>
    </GameSubpage>
  );
};

export default PracticeTopics;
