import { useState, type ChangeEvent } from 'react';
import { IonButton, IonIcon } from '@ionic/react';
import { cameraOutline, closeCircle } from 'ionicons/icons';
import './ProfilePhotoInput.css';

const ProfilePhotoInput: React.FC = () => {
  const [preview, setPreview] = useState('');

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    setPreview(file ? URL.createObjectURL(file) : '');
  };

  const clearPhoto = () => {
    const input = document.getElementById('profile-photo-input') as HTMLInputElement | null;
    if (input) input.value = '';
    setPreview('');
  };

  return (
    <div className="profile-photo-field">
      <input
        id="profile-photo-input"
        className="profile-photo-field__input"
        type="file"
        name="profilePhoto"
        accept="image/jpeg,image/png,image/webp"
        capture="user"
        onChange={handleChange}
        aria-label="Optional profile photo"
      />
      {preview ? (
        <div className="profile-photo-field__selected">
          <img src={preview} alt="Profile photo preview" />
          <span>Photo selected</span>
          <IonButton fill="clear" type="button" onClick={clearPhoto} aria-label="Remove profile photo">
            <IonIcon icon={closeCircle} slot="icon-only" />
          </IonButton>
        </div>
      ) : (
        <label className="profile-photo-field__prompt" htmlFor="profile-photo-input">
          <IonIcon icon={cameraOutline} aria-hidden="true" />
          <span><strong>Add a profile photo</strong><small>Optional · take a selfie with your camera</small></span>
        </label>
      )}
    </div>
  );
};

export default ProfilePhotoInput;
