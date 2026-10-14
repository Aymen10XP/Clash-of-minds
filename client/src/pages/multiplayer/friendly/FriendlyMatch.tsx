import { useCallback, useEffect, useMemo, useState } from 'react';
import { IonBadge, IonButton, IonIcon, IonInput, IonSpinner } from '@ionic/react';
import {
  checkmarkCircleOutline,
  closeCircleOutline,
  paperPlaneOutline,
  refreshOutline,
  searchOutline,
} from 'ionicons/icons';
import { useNavigate } from 'react-router-dom';
import GameSubpage from '../../../components/game/GameSubpage';
import {
  cancelMatchInvitation,
  fetchInvitations,
  fetchMatches,
  respondToMatchInvitation,
  searchMultiplayerPlayers,
  sendMatchInvitation,
  type KnowledgeMatch,
  type MatchInvitation,
  type MultiplayerPlayer,
} from '../../../features/multiplayer/api';
import { usePressNavigation } from '../../../hooks/usePressNavigation';
import { appRoutes } from '../../../routing/routes';
import './FriendlyMatch.css';

const POLL_INTERVAL_MS = 5_000;

const FriendlyMatch: React.FC = () => {
  const navigate = useNavigate();
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });
  const [query, setQuery] = useState('');
  const [players, setPlayers] = useState<MultiplayerPlayer[]>([]);
  const [invitations, setInvitations] = useState<MatchInvitation[]>([]);
  const [matches, setMatches] = useState<KnowledgeMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [actionId, setActionId] = useState<string | number | null>(null);
  const [error, setError] = useState('');

  const refreshLobby = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const [nextInvitations, nextMatches] = await Promise.all([
        fetchInvitations(),
        fetchMatches(),
      ]);
      setInvitations(nextInvitations);
      setMatches(nextMatches);
      setError('');
    } catch (caught) {
      if (!quiet) setError(caught instanceof Error ? caught.message : 'Unable to load the lobby.');
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshLobby();
    const interval = window.setInterval(() => void refreshLobby(true), POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [refreshLobby]);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setPlayers([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    const timeout = window.setTimeout(() => {
      void searchMultiplayerPlayers(trimmed)
        .then(setPlayers)
        .catch((caught) => setError(caught instanceof Error ? caught.message : 'Player search failed.'))
        .finally(() => setSearching(false));
    }, 250);
    return () => window.clearTimeout(timeout);
  }, [query]);

  const pendingIncoming = useMemo(() => invitations.filter(
    (invitation) => invitation.direction === 'incoming' && invitation.status === 'pending',
  ), [invitations]);
  const pendingOutgoing = useMemo(() => invitations.filter(
    (invitation) => invitation.direction === 'outgoing' && invitation.status === 'pending',
  ), [invitations]);
  const pendingPlayerIds = useMemo(() => new Set(invitations
    .filter((invitation) => invitation.status === 'pending')
    .flatMap((invitation) => [invitation.sender.id, invitation.recipient.id])), [invitations]);

  const runAction = async (id: string | number, action: () => Promise<unknown>) => {
    setActionId(id);
    setError('');
    try {
      await action();
      await refreshLobby(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The action could not be completed.');
    } finally {
      setActionId(null);
    }
  };

  return (
    <GameSubpage
      eyebrow="Private duel"
      title="Friendly Match"
      onBack={() => goBackAfterPress(appRoutes.multiplayer)}
      className="friendly-match-page"
    >
      <div className="friendly-lobby">
        <section className="friendly-lobby__hero">
          <div>
            <p className="friendly-lobby__kicker">Challenge desk</p>
            <h2>Find your next rival</h2>
            <p>Invite another player, meet in a private room, and ready up for battle.</p>
          </div>
          <IonButton fill="clear" aria-label="Refresh lobby" onClick={() => void refreshLobby()}>
            <IonIcon icon={refreshOutline} slot="icon-only" />
          </IonButton>
        </section>

        {error && <div className="friendly-lobby__error" role="alert">{error}</div>}

        <section className="friendly-panel" aria-labelledby="player-search-title">
          <div className="friendly-panel__heading">
            <div><span>01</span><h3 id="player-search-title">Find a player</h3></div>
          </div>
          <IonInput
            className="friendly-search"
            value={query}
            placeholder="Search by username"
            aria-label="Search players by username"
            onIonInput={(event) => setQuery(String(event.detail.value ?? ''))}
          >
            <IonIcon icon={searchOutline} slot="start" />
            {searching && <IonSpinner name="dots" slot="end" />}
          </IonInput>
          {query.trim() && !searching && (
            <div className="friendly-list">
              {players.length === 0 && <p className="friendly-empty">No challengers found.</p>}
              {players.map((player) => {
                const pending = pendingPlayerIds.has(player.id);
                return (
                  <article className="friendly-player" key={player.id}>
                    <div className="friendly-avatar">{player.username.slice(0, 2).toUpperCase()}</div>
                    <div><strong>{player.username}</strong><span>{player.country}</span></div>
                    <IonButton
                      size="small"
                      disabled={pending || actionId === player.id}
                      onClick={() => void runAction(player.id, () => sendMatchInvitation(player.id))}
                    >
                      <IonIcon icon={paperPlaneOutline} slot="start" />
                      {pending ? 'Invited' : 'Challenge'}
                    </IonButton>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <section className="friendly-panel" aria-labelledby="invitation-title">
          <div className="friendly-panel__heading">
            <div><span>02</span><h3 id="invitation-title">Invitations</h3></div>
            <IonBadge>{pendingIncoming.length + pendingOutgoing.length}</IonBadge>
          </div>
          {loading ? (
            <div className="friendly-loading"><IonSpinner name="crescent" /> Loading lobby</div>
          ) : (
            <div className="friendly-list">
              {pendingIncoming.length === 0 && pendingOutgoing.length === 0 && (
                <p className="friendly-empty">No pending invitations.</p>
              )}
              {pendingIncoming.map((invitation) => (
                <article className="friendly-invite" key={invitation.id}>
                  <div><small>Incoming challenge</small><strong>{invitation.sender.username}</strong></div>
                  <div className="friendly-invite__actions">
                    <IonButton
                      size="small"
                      aria-label={`Accept challenge from ${invitation.sender.username}`}
                      disabled={actionId === invitation.id}
                      onClick={() => void runAction(invitation.id, () => respondToMatchInvitation(invitation.id, 'accept'))}
                    ><IonIcon icon={checkmarkCircleOutline} slot="icon-only" /></IonButton>
                    <IonButton
                      size="small"
                      fill="outline"
                      color="medium"
                      aria-label={`Decline challenge from ${invitation.sender.username}`}
                      disabled={actionId === invitation.id}
                      onClick={() => void runAction(invitation.id, () => respondToMatchInvitation(invitation.id, 'decline'))}
                    ><IonIcon icon={closeCircleOutline} slot="icon-only" /></IonButton>
                  </div>
                </article>
              ))}
              {pendingOutgoing.map((invitation) => (
                <article className="friendly-invite" key={invitation.id}>
                  <div><small>Waiting for</small><strong>{invitation.recipient.username}</strong></div>
                  <IonButton
                    size="small"
                    fill="clear"
                    color="medium"
                    disabled={actionId === invitation.id}
                    onClick={() => void runAction(invitation.id, () => cancelMatchInvitation(invitation.id))}
                  >Cancel</IonButton>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="friendly-panel friendly-panel--matches" aria-labelledby="match-title">
          <div className="friendly-panel__heading">
            <div><span>03</span><h3 id="match-title">Battle rooms</h3></div>
            <IonBadge>{matches.length}</IonBadge>
          </div>
          <div className="friendly-list">
            {!loading && matches.length === 0 && <p className="friendly-empty">Accepted challenges will appear here.</p>}
            {matches.map((match) => {
              const opponent = match.participants.find((participant) => !participant.isCurrentUser);
              return (
                <article className="friendly-match" key={match.id}>
                  <div><small>{match.status === 'waiting' ? 'Room open' : match.status}</small><strong>vs {opponent?.username ?? 'Challenger'}</strong></div>
                  <IonButton size="small" onClick={() => navigate(`/multiplayer/match/${match.id}`)}>Open room</IonButton>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </GameSubpage>
  );
};

export default FriendlyMatch;
