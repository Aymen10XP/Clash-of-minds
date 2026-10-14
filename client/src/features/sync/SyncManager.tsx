import { useCallback, useEffect, useRef, useState } from 'react';
import { IonButton, IonContent, IonModal, IonSpinner } from '@ionic/react';
import { useAuth } from '../auth/context';
import {
  getPendingRunCount,
  refreshOfflineCatalog,
  synchronizeOfflineRuns,
} from './api';
import './SyncManager.css';

type SyncState = 'idle' | 'syncing' | 'success' | 'error';

const SyncManager: React.FC = () => {
  const { status, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>('idle');
  const [message, setMessage] = useState('');
  const inProgress = useRef(false);

  const synchronize = useCallback(async () => {
    if (!user || navigator.onLine === false || inProgress.current) return;
    inProgress.current = true;
    const pendingCount = getPendingRunCount(user.id);
    if (pendingCount) {
      setIsOpen(true);
      setSyncState('syncing');
      setMessage(`Saving ${pendingCount} offline ${pendingCount === 1 ? 'game' : 'games'} to your account…`);
    }

    try {
      const syncedCount = await synchronizeOfflineRuns(user);
      if (syncedCount) {
        setSyncState('success');
        setMessage(`${syncedCount} offline ${syncedCount === 1 ? 'game was' : 'games were'} synchronized.`);
        window.setTimeout(() => setIsOpen(false), 1100);
      }
      await refreshOfflineCatalog(user).catch(() => undefined);
    } catch (error) {
      if (pendingCount) {
        setSyncState('error');
        setMessage(error instanceof Error ? error.message : 'Synchronization failed.');
      }
    } finally {
      inProgress.current = false;
    }
  }, [user]);

  useEffect(() => {
    if (status !== 'authenticated') return;
    void synchronize();
    window.addEventListener('online', synchronize);
    return () => window.removeEventListener('online', synchronize);
  }, [status, synchronize]);

  return (
    <IonModal isOpen={isOpen} backdropDismiss={syncState !== 'syncing'} className="sync-modal">
      <IonContent className="ion-padding">
        <div className="sync-modal__content" role="status" aria-live="polite">
          {syncState === 'syncing' && <IonSpinner name="crescent" />}
          <p className="sync-modal__eyebrow">Back online</p>
          <h2>Synchronization</h2>
          <p>{message}</p>
          {syncState === 'error' && (
            <>
              <IonButton expand="block" onClick={() => void synchronize()}>Try again</IonButton>
              <IonButton expand="block" fill="clear" onClick={() => setIsOpen(false)}>Later</IonButton>
            </>
          )}
        </div>
      </IonContent>
    </IonModal>
  );
};

export default SyncManager;
