import { useEffect, useState, type FormEvent } from 'react';
import { IonButton, IonIcon } from '@ionic/react';
import { cameraOutline, closeCircleOutline } from 'ionicons/icons';
import GameSubpage from '../../components/game/GameSubpage';
import { useAuth } from '../../features/auth/context';
import { usePressNavigation } from '../../hooks/usePressNavigation';
import { appRoutes } from '../../routing/routes';
import './Settings.css';

const Settings: React.FC = () => {
  const { user, updateProfile } = useAuth();
  const { goBackAfterPress } = usePressNavigation({ delay: 140, feedback: 'light' });
  const [username, setUsername] = useState(user?.username ?? '');
  const [selectedPhoto, setSelectedPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState(user?.profilePhoto ?? '');
  const [photoFailed, setPhotoFailed] = useState(false);
  const [removePhoto, setRemovePhoto] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setUsername(user?.username ?? '');
    setPhotoPreview(user?.profilePhoto ?? '');
  }, [user?.username, user?.profilePhoto]);

  useEffect(() => setPhotoFailed(false), [photoPreview]);

  useEffect(() => () => {
    if (photoPreview.startsWith('blob:')) URL.revokeObjectURL(photoPreview);
  }, [photoPreview]);

  const handlePhotoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0] ?? null;
    setSelectedPhoto(file);
    setPhotoPreview(file ? URL.createObjectURL(file) : (user?.profilePhoto ?? ''));
    setRemovePhoto(false);
    setError('');
    setSaved(false);
  };

  const handleRemovePhoto = () => {
    const input = document.getElementById('settings-profile-photo') as HTMLInputElement | null;
    if (input) input.value = '';
    setSelectedPhoto(null);
    setPhotoPreview('');
    setRemovePhoto(Boolean(user?.profilePhoto));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setSaved(false);
    setSaving(true);
    try {
      const profilePhoto = selectedPhoto
        ? await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result));
          reader.onerror = () => reject(new Error('Unable to read the selected photo.'));
          reader.readAsDataURL(selectedPhoto);
        })
        : undefined;
      await updateProfile({ username: username.trim(), profilePhoto, removeProfilePhoto: removePhoto });
      setSelectedPhoto(null);
      setRemovePhoto(false);
      setSaved(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to save profile changes.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <GameSubpage
      eyebrow="Player account"
      title="Settings"
      onBack={() => goBackAfterPress(appRoutes.home)}
      className="settings-page"
    >
      <section className="settings-profile" aria-label="Edit player profile">
        <p className="settings-profile__intro">Make your player profile yours.</p>
        <form className="settings-profile__form" onSubmit={handleSubmit}>
          <div className="settings-profile__photo-row">
            {photoPreview && !photoFailed ? (
              <img
                className="settings-profile__avatar"
                src={photoPreview}
                alt="Profile preview"
                onError={() => setPhotoFailed(true)}
              />
            ) : (
              <div className="settings-profile__avatar settings-profile__avatar--empty" aria-hidden="true">
                {(username.trim()[0] ?? '?').toUpperCase()}
              </div>
            )}
            <div className="settings-profile__photo-actions">
              <input
                id="settings-profile-photo"
                className="settings-profile__file"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                capture="user"
                onChange={handlePhotoChange}
                aria-label="Choose a profile photo"
              />
              <label className="settings-profile__choose" htmlFor="settings-profile-photo">
                <IonIcon icon={cameraOutline} aria-hidden="true" />
                <span>{photoPreview ? 'Change photo' : 'Take or choose a photo'}</span>
              </label>
              {photoPreview && (
                <IonButton className="settings-profile__remove" fill="clear" type="button" onClick={handleRemovePhoto}>
                  <IonIcon icon={closeCircleOutline} slot="start" />
                  Remove
                </IonButton>
              )}
            </div>
          </div>

          <label className="settings-profile__label" htmlFor="settings-username">Player name</label>
          <input
            id="settings-username"
            className="settings-profile__username"
            type="text"
            minLength={3}
            maxLength={150}
            autoComplete="username"
            value={username}
            onChange={(event) => {
              setUsername(event.currentTarget.value);
              setError('');
              setSaved(false);
            }}
            required
          />

          <IonButton className="settings-profile__save" expand="block" type="submit" disabled={saving || !user}>
            {saving ? 'Saving…' : 'Save profile'}
          </IonButton>
          {error && <p className="settings-profile__notice settings-profile__notice--error" role="alert">{error}</p>}
          {saved && <p className="settings-profile__notice" role="status">Profile updated.</p>}
        </form>
      </section>
    </GameSubpage>
  );
};

export default Settings;
