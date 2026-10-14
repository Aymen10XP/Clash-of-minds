import { useCallback, useEffect, useState } from 'react';
import { IonAlert, IonButton, IonIcon, IonSpinner } from '@ionic/react';
import {
  checkmarkCircleOutline,
  flashOutline,
  heartOutline,
  refreshOutline,
  timeOutline,
} from 'ionicons/icons';
import { useNavigate, useParams } from 'react-router-dom';
import GameSubpage from '../../../components/game/GameSubpage';
import {
  closeMatchRoom,
  fetchMatch,
  markMatchReady,
  MultiplayerApiError,
  requestMatchRematch,
  submitMatchAnswer,
  type KnowledgeMatch,
} from '../../../features/multiplayer/api';
import { appRoutes } from '../../../routing/routes';
import './MatchRoom.css';

const MatchRoom: React.FC = () => {
  const { matchId = '' } = useParams<{ matchId: string }>();
  const navigate = useNavigate();
  const [match, setMatch] = useState<KnowledgeMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedChoiceId, setSelectedChoiceId] = useState<number | null>(null);
  const [remainingMs, setRemainingMs] = useState(0);
  const [questionRemainingMs, setQuestionRemainingMs] = useState(0);
  const [showCloseConfirmation, setShowCloseConfirmation] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const nextMatch = await fetchMatch(matchId);
      if (nextMatch.rematchMatchId) {
        navigate(`/multiplayer/match/${nextMatch.rematchMatchId}`, { replace: true });
        return;
      }
      setQuestionRemainingMs(nextMatch.currentRound?.remainingMs ?? 0);
      setMatch(nextMatch);
      setError('');
    } catch (caught) {
      if (caught instanceof MultiplayerApiError && caught.status === 404) {
        navigate(appRoutes.multiplayerFriendly, { replace: true });
        return;
      }
      if (!quiet) setError(caught instanceof Error ? caught.message : 'Unable to open the match.');
    } finally {
      if (!quiet) setLoading(false);
    }
  }, [matchId, navigate]);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(true), 1_000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  useEffect(() => {
    setRemainingMs(match?.remainingMs ?? 0);
  }, [match?.remainingMs]);

  useEffect(() => {
    setQuestionRemainingMs(match?.currentRound?.remainingMs ?? 0);
  }, [match?.currentRound?.remainingMs, match?.currentRound?.sequence]);

  useEffect(() => {
    if (match?.status !== 'active') return;
    const interval = window.setInterval(() => {
      setRemainingMs((value) => Math.max(0, value - 250));
    }, 250);
    return () => window.clearInterval(interval);
  }, [match?.status]);

  useEffect(() => {
    if (match?.status !== 'active' || !match.currentRound) return;
    const interval = window.setInterval(() => {
      setQuestionRemainingMs((value) => Math.max(0, value - 100));
    }, 100);
    return () => window.clearInterval(interval);
  }, [match?.currentRound, match?.status]);

  useEffect(() => {
    setSelectedChoiceId(null);
  }, [match?.currentRound?.sequence]);

  const handleReady = async () => {
    setSubmitting(true);
    try {
      setMatch(await markMatchReady(matchId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not update readiness.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAnswer = async (choiceId: number) => {
    if (!match?.currentRound || match.currentRound.hasAnswered || submitting || questionRemainingMs <= 0) return;
    setSelectedChoiceId(choiceId);
    setSubmitting(true);
    setError('');
    try {
      setMatch(await submitMatchAnswer(matchId, match.currentRound.question.id, choiceId));
    } catch (caught) {
      if (caught instanceof MultiplayerApiError && caught.status === 409) {
        await refresh(true);
        return;
      }
      setError(caught instanceof Error ? caught.message : 'Your answer could not be submitted.');
      setSelectedChoiceId(null);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRematch = async () => {
    setSubmitting(true);
    setError('');
    try {
      const nextMatch = await requestMatchRematch(matchId);
      if (nextMatch.rematchMatchId) {
        navigate(`/multiplayer/match/${nextMatch.rematchMatchId}`, { replace: true });
      } else {
        setMatch(nextMatch);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not request a rematch.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseRoom = async () => {
    setShowCloseConfirmation(false);
    setSubmitting(true);
    try {
      await closeMatchRoom(matchId);
      navigate(appRoutes.multiplayerFriendly, { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not close the room.');
      setSubmitting(false);
    }
  };

  const currentPlayer = match?.participants.find((participant) => participant.isCurrentUser);
  const timerSeconds = Math.ceil(remainingMs / 1000);
  const timerLabel = `${Math.floor(timerSeconds / 60)}:${String(timerSeconds % 60).padStart(2, '0')}`;
  const questionTimerSeconds = Math.ceil(questionRemainingMs / 1000);

  return (
    <GameSubpage
      eyebrow="Private battle room"
      title="Knowledge Duel"
      onBack={() => setShowCloseConfirmation(true)}
      className="match-room-page"
    >
      <section className="match-room" aria-live="polite">
        {loading && <div className="match-room__state"><IonSpinner name="crescent" /> Opening battle room</div>}
        {error && (
          <div className="match-room__state match-room__state--error">
            <p>{error}</p>
            <IonButton onClick={() => void refresh()}><IonIcon icon={refreshOutline} slot="start" />Try again</IonButton>
          </div>
        )}
        {match && !loading && (
          <>
            <header className="match-room__status">
              <span>{match.status === 'waiting' ? 'Waiting room' : 'Match status'}</span>
              {match.status === 'active' ? (
                <strong className={timerSeconds <= 30 ? 'is-critical' : ''}>
                  <IonIcon icon={timeOutline} />{timerLabel}
                </strong>
              ) : <strong>{match.status}</strong>}
            </header>
            <div className="match-room__versus">
              {match.participants.map((participant, index) => (
                <div className="match-contender" key={participant.id}>
                  <div className="match-contender__avatar">{participant.username.slice(0, 2).toUpperCase()}</div>
                  <small>{participant.isCurrentUser ? 'You' : participant.country}</small>
                  <strong>{participant.username}</strong>
                  <div className="match-contender__hearts" aria-label={`${participant.hearts} hearts`}>
                    {[0, 1, 2].map((heart) => (
                      <IonIcon
                        icon={heartOutline}
                        key={heart}
                        className={heart < participant.hearts ? 'is-full' : 'is-lost'}
                      />
                    ))}
                  </div>
                  <span className={participant.ready ? 'is-ready' : ''}>
                    <IonIcon icon={participant.ready ? checkmarkCircleOutline : flashOutline} />
                    {participant.ready ? 'Ready' : 'Preparing'}
                  </span>
                  {index === 0 && <b>VS</b>}
                </div>
              ))}
            </div>
            {match.status === 'waiting' && (
              <div className="match-room__controls">
                <p>{currentPlayer?.ready ? 'Waiting for your opponent to ready up.' : 'When both players are ready, the battle begins.'}</p>
                <IonButton
                  expand="block"
                  disabled={Boolean(currentPlayer?.ready) || submitting}
                  onClick={() => void handleReady()}
                >
                  {submitting ? <IonSpinner name="dots" /> : 'I’m ready'}
                </IonButton>
              </div>
            )}
            {match.status === 'active' && (
              <div className="match-game">
                {match.lastRound && (
                  <div className="match-game__round-result">
                    {match.lastRound.winnerId === null
                      ? 'No correct answer — next round'
                      : match.lastRound.winnerId === currentPlayer?.id
                        ? 'You won the last round'
                        : 'Opponent won the last round'}
                  </div>
                )}
                {match.currentRound && (
                  <>
                    <div className="match-game__meta">
                      <span>Round {match.currentRound.sequence}</span>
                      <span>{match.currentRound.question.topic.title}</span>
                      <span>{match.currentRound.question.difficulty}</span>
                      <span className={questionTimerSeconds <= 5 ? 'match-game__question-timer is-critical' : 'match-game__question-timer'}>
                        <IonIcon icon={timeOutline} /> {questionTimerSeconds}s
                      </span>
                    </div>
                    <h2>{match.currentRound.question.prompt}</h2>
                    <div className="match-game__answers" role="group" aria-label="Possible answers">
                      {match.currentRound.question.choices.map((choice, index) => (
                        <button
                          type="button"
                          key={choice.id}
                          className={selectedChoiceId === choice.id || match.currentRound?.selectedChoiceId === choice.id ? 'is-selected' : ''}
                          disabled={match.currentRound?.hasAnswered || submitting || questionRemainingMs <= 0}
                          onClick={() => void handleAnswer(choice.id)}
                        >
                          <span>{String.fromCharCode(65 + index)}</span>
                          <strong>{choice.text}</strong>
                        </button>
                      ))}
                    </div>
                    {match.currentRound.hasAnswered && (
                      <p className="match-game__locked">Answer locked. Waiting for your opponent...</p>
                    )}
                  </>
                )}
              </div>
            )}
            {match.status === 'completed' && (
              <div className="match-result" role="dialog" aria-modal="true" aria-labelledby="match-result-title">
                <IonIcon icon={match.winnerId === currentPlayer?.id ? flashOutline : heartOutline} />
                <p>
                  {match.endReason === 'time'
                    ? 'Time expired'
                    : match.endReason === 'forfeit' ? 'Opponent left the room' : 'Final heart lost'}
                </p>
                <h2 id="match-result-title">
                  {match.winnerId === null
                    ? 'Draw'
                    : match.winnerId === currentPlayer?.id ? 'Winner!' : 'Game over'}
                </h2>
                <p>
                  {match.winnerId === null
                    ? 'You finished with the same number of hearts.'
                    : match.winnerId === currentPlayer?.id
                      ? 'You leave the arena victorious.'
                      : 'Your opponent won this duel.'}
                </p>
                <IonButton
                  expand="block"
                  disabled={Boolean(currentPlayer?.rematchRequested) || submitting}
                  onClick={() => void handleRematch()}
                >
                  {currentPlayer?.rematchRequested ? 'Waiting for opponent...' : 'Rematch'}
                </IonButton>
                <IonButton fill="clear" expand="block" onClick={() => setShowCloseConfirmation(true)}>
                  Close room
                </IonButton>
              </div>
            )}
          </>
        )}
      </section>
      <IonAlert
        isOpen={showCloseConfirmation}
        onDidDismiss={() => setShowCloseConfirmation(false)}
        header="Close battle room?"
        message="Are you sure you want to close this room? It will be permanently terminated after both players close it."
        buttons={[
          { text: 'Stay', role: 'cancel' },
          { text: 'Close room', role: 'destructive', handler: () => void handleCloseRoom() },
        ]}
      />
    </GameSubpage>
  );
};

export default MatchRoom;
