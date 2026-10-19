import { Capacitor } from '@capacitor/core';
import {
  Camera,
  CameraDirection,
  CameraErrorCode,
  EncodingType,
  MediaTypeSelection,
  type MediaResult,
} from '@capacitor/camera';

const MAX_PROFILE_PHOTO_BYTES = 5 * 1024 * 1024;
const SUPPORTED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

const blobToDataUrl = (blob: Blob) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result));
  reader.onerror = () => reject(new Error('Unable to read the selected photo.'));
  reader.readAsDataURL(blob);
});

export const mediaResultToDataUrl = async (result: MediaResult): Promise<string> => {
  const source = result.webPath ?? (result.uri ? Capacitor.convertFileSrc(result.uri) : '');
  if (source) {
    const response = await fetch(source);
    if (!response.ok) throw new Error('Unable to read the selected photo.');
    const blob = await response.blob();
    if (!SUPPORTED_IMAGE_TYPES.has(blob.type.toLowerCase())) {
      throw new Error('Choose a JPEG, PNG, or WebP image.');
    }
    if (blob.size > MAX_PROFILE_PHOTO_BYTES) throw new Error('Profile photos may be up to 5 MB.');
    return blobToDataUrl(blob);
  }

  if (result.thumbnail) {
    const format = result.metadata?.format?.toLowerCase() || 'jpeg';
    const mimeType = format === 'jpg' ? 'image/jpeg' : `image/${format}`;
    return `data:${mimeType};base64,${result.thumbnail}`;
  }
  throw new Error('The selected photo could not be read.');
};

const sharedOptions = {
  quality: 85,
  targetWidth: 1280,
  targetHeight: 1280,
  correctOrientation: true,
  includeMetadata: true,
} as const;

export const takeProfilePhoto = async () => {
  const result = await Camera.takePhoto({
    ...sharedOptions,
    encodingType: EncodingType.JPEG,
    cameraDirection: CameraDirection.Front,
    editable: 'no',
    saveToGallery: false,
    webUseInput: true,
  });
  return mediaResultToDataUrl(result);
};

export const chooseProfilePhoto = async () => {
  const result = await Camera.chooseFromGallery({
    ...sharedOptions,
    mediaType: MediaTypeSelection.Photo,
    allowMultipleSelection: false,
    editable: 'no',
    webUseInput: true,
  });
  const photo = result.results[0];
  if (!photo) throw new Error('No photo was selected.');
  return mediaResultToDataUrl(photo);
};

export const isPhotoSelectionCancelled = (error: unknown) => {
  if (!error || typeof error !== 'object') return false;
  const code = 'code' in error ? String(error.code) : '';
  const message = 'message' in error ? String(error.message).toLowerCase() : '';
  return code === CameraErrorCode.TakePhotoCancelled
    || code === CameraErrorCode.ChooseMediaCancelled
    || message.includes('cancel');
};
