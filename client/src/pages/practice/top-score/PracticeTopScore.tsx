import { useCallback, useEffect, useRef, useState } from 'react';
import { IonButton, IonIcon, IonSpinner } from '@ionic/react';
import { refreshOutline, trophyOutline } from 'ionicons/icons';
import GameSubpage from '../../../components/game/GameSubpage';
import {
  answerTopScore,
  quitTopScore,
  startTopScore,
  type QuizQuestion,
} from '../../../features/quiz/api';
import { playAnswerFeedback } from '../../../features/quiz/feedback';
import { usePressNavigation } from '../../../hooks/usePressNavigation';
import { appRoutes } from '../../../routing/routes';
import './PracticeTopScore.css';

type GamePhase = 'loading' | 'playing' | 'answering' | 'feedback' | 'gameover' | 'error';

const FALLBACK_TIME_LIMIT = 10_000;
const CORRECT_FEEDBACK_MS = 900;
const WRONG_FEEDBACK_MS = 650;

const PracticeTopScore: React.FC = () => {
  const { goBackAfterPress } = usePressNavigation({ delay: 100, feedback: 'light' });
  const [phase, setPhase] = useState<GamePhase>('loading');
  const [question, setQuestion] = useState<QuizQuestion | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);
  const [remainingMs, setRemainingMs] = useState(FALLBACK_TIME_LIMIT);
  const [selectedChoiceId, setSelectedChoiceId] = useState<number | null>(null);
  const [correctChoiceId, setCorrectChoiceId] = useState<number | null>(null);
  const [timedOut, setTimedOut] = useState(false);
  const [error, setError] = useState('');
  const deadlineRef = useRef(0);
  const timeLimitRef = useRef(FALLBACK_TIME_LIMIT);
  const phaseRef = useRef<GamePhase>('loading');
  const feedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const changePhase = useCallback((nextPhase: GamePhase) => {
    phaseRef.current = nextPhase;
    setPhase(nextPhase);
  }, []);

  const beginQuestion = useCallback((nextQuestion: QuizQuestion) => {
    setQuestion(nextQuestion);
    setSelectedChoiceId(null);
    setCorrectChoiceId(null);
    setTimedOut(false);
    setRemainingMs(timeLimitRef.current);
    deadlineRef.current = Date.now() + timeLimitRef.current;
    changePhase('playing');
  }, [changePhase]);

  const startGame = useCallback(async () => {
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    changePhase('loading');
    setError('');
    setQuestion(null);
    try {
      const game = await startTopScore();
      setRunId(game.runId);
      setScore(game.score);
      setBestScore(game.bestScore);
      timeLimitRef.current = game.timeLimitMs;
      beginQuestion(game.question);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to start Top Score.');
      changePhase('error');
    }
  }, [beginQuestion, changePhase]);

  useEffect(() => {
    void startGame();
    return () => {
      if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    };
  }, [startGame]);

  const submitAnswer = useCallback(async (choiceId: number | null) => {
    if (phaseRef.current !== 'playing' || !runId || !question) return;
    changePhase('answering');
    setSelectedChoiceId(choiceId);
    setTimedOut(choiceId === null);

    try {
      const result = await answerTopScore(runId, question.id, choiceId);
      setScore(result.score);
      setBestScore(result.bestScore);
      setCorrectChoiceId(result.correctChoiceId);
      setTimedOut(result.timedOut);
      changePhase('feedback');
      playAnswerFeedback(result.correct ? 'correct' : 'wrong');

      feedbackTimerRef.current = setTimeout(() => {
        if (result.correct && result.question) beginQuestion(result.question);
        else changePhase('gameover');
      }, result.correct ? CORRECT_FEEDBACK_MS : WRONG_FEEDBACK_MS);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Your answer could not be submitted.');
      changePhase('error');
    }
  }, [beginQuestion, changePhase, question, runId]);

  useEffect(() => {
    if (phase !== 'playing') return;
    const tick = () => {
      const nextRemaining = Math.max(0, deadlineRef.current - Date.now());
      setRemainingMs(nextRemaining);
      if (nextRemaining === 0) void submitAnswer(null);
    };
    tick();
    const interval = window.setInterval(tick, 50);
    return () => window.clearInterval(interval);
  }, [phase, submitAnswer]);

  const handleBack = () => {
    if (runId && !['gameover', 'loading'].includes(phase)) {
      void quitTopScore(runId).catch(() => undefined);
    }
    goBackAfterPress(appRoutes.practice);
  };

  const timerSeconds = Math.ceil(remainingMs / 1000);
  const progress = Math.max(0, Math.min(1, remainingMs / timeLimitRef.current));

  return (
    <GameSubpage
      eyebrow="Endless ladder"
      title="Top Score"
      onBack={handleBack}
      className="practice-top-score-page"
    >
      <section className="top-score-game" aria-live="polite">
        <div className="top-score-game__hud">
          <div><span>Score</span><strong>{score}</strong></div>
          <div className="top-score-game__best">
            <IonIcon icon={trophyOutline} /><span>Best</span><strong>{bestScore}</strong>
          </div>
          <div className={`top-score-game__clock ${timerSeconds <= 3 ? 'is-critical' : ''}`}>
            <span>Time</span><strong>{timerSeconds}</strong>
          </div>
        </div>

        <div className="top-score-game__timer" aria-label={`${timerSeconds} seconds remaining`}>
          <span style={{ transform: `scaleX(${progress})` }} />
        </div>

        {phase === 'loading' && (
          <div className="top-score-game__status">
            <IonSpinner name="crescent" /><p>Preparing the archive…</p>
          </div>
        )}

        {phase === 'error' && (
          <div className="top-score-game__status top-score-game__status--error">
            <p>{error}</p>
            <IonButton onClick={() => void startGame()}>
              <IonIcon icon={refreshOutline} slot="start" />Try again
            </IonButton>
          </div>
        )}

        {question && phase !== 'loading' && phase !== 'error' && (
          <div className="top-score-game__round">
            <div className="top-score-game__category">
              <span>{question.topic.title}</span><span>{question.difficulty}</span>
            </div>
            <h2>{question.prompt}</h2>
            <div className="top-score-game__answers" role="group" aria-label="Possible answers">
              {question.choices.map((choice, index) => {
                const isCorrect = correctChoiceId === choice.id;
                const isWrong = selectedChoiceId === choice.id && correctChoiceId !== null && !isCorrect;
                return (
                  <button
                    key={choice.id}
                    type="button"
                    className={`top-score-answer ${isCorrect ? 'is-correct' : ''} ${isWrong ? 'is-wrong' : ''}`}
                    disabled={phase !== 'playing'}
                    onClick={() => void submitAnswer(choice.id)}
                  >
                    <span>{String.fromCharCode(65 + index)}</span>
                    <strong>{choice.text}</strong>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {phase === 'answering' && (
          <div className="top-score-game__sending"><IonSpinner name="dots" /></div>
        )}

        {phase === 'gameover' && (
          <div className="top-score-result" role="dialog" aria-modal="true" aria-labelledby="top-score-result-title">
            <div className="top-score-result__panel">
              <span className="top-score-result__eyebrow">{timedOut ? 'Time expired' : 'Run ended'}</span>
              <h2 id="top-score-result-title">Final score</h2>
              <strong className="top-score-result__score">{score}</strong>
              <p>Best score: {bestScore}</p>
              <IonButton expand="block" onClick={() => void startGame()}>Play again</IonButton>
              <IonButton expand="block" fill="clear" onClick={handleBack}>Back to modes</IonButton>
            </div>
          </div>
        )}
      </section>
    </GameSubpage>
  );
};

export default PracticeTopScore;
