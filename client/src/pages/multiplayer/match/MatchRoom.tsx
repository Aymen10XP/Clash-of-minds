import { useCallback, useEffect, useState } from 'react';
import { IonButton, IonIcon, IonSpinner } from '@ionic/react';
import { checkmarkCircleOutline, flashOutline, refreshOutline } from 'ionicons/icons';
import { useParams } from 'react-router-dom';
import GameSubpage from '../../../components/game/GameSubpage';
import {
  fetchMatch,
  markMatchReady,
  type KnowledgeMatch,
} from '../../../features/multiplayer/api';
import { usePressNavigation } from '../../../hooks/usePressNavigation';
import { appRoutes } from '../../../routing/routes';
import './MatchRoom.css';

const MatchRoom: React.FC = () => {
  const { matchId = '' } = useParams<{ matchId: string }>();
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });
  const [match, setMatch] = useState<KnowledgeMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      setMatch(await fetchMatch(matchId));
      setError('');
    } catch (caught) {
      if (!quiet) setError(caught instanceof Error ? caught.message : 'Unable to open the match.');
    } finally {
      if (!quiet) setLoading(false);
    }
  }, [matchId]);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(true), 3_000);
    return () => window.clearInterval(interval);
  }, [refresh]);

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

  const currentPlayer = match?.participants.find((participant) => participant.isCurrentUser);

  return (
    <GameSubpage
      eyebrow="Private battle room"
      title="Knowledge Duel"
      onBack={() => goBackAfterPress(appRoutes.multiplayerFriendly)}
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
              <strong>{match.status}</strong>
            </header>
            <div className="match-room__versus">
              {match.participants.map((participant, index) => (
                <div className="match-contender" key={participant.id}>
                  <div className="match-contender__avatar">{participant.username.slice(0, 2).toUpperCase()}</div>
                  <small>{participant.isCurrentUser ? 'You' : participant.country}</small>
                  <strong>{participant.username}</strong>
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
              <div className="match-room__active">
                <IonIcon icon={flashOutline} />
                <h2>Battle initialized</h2>
                <p>The room and both participants are synchronized. Question rounds can now attach to this active match.</p>
              </div>
            )}
          </>
        )}
      </section>
    </GameSubpage>
  );
};

export default MatchRoom;
