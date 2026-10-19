import { CameraErrorCode, MediaType, type MediaResult } from '@capacitor/camera';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { isPhotoSelectionCancelled, mediaResultToDataUrl } from './camera';

describe('profile camera integration', () => {
  afterEach(() => vi.restoreAllMocks());

  it('converts a Capacitor media result into an uploadable data URL', async () => {
    const blob = new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])], { type: 'image/jpeg' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, blob: async () => blob }));
    const result: MediaResult = {
      type: MediaType.Photo,
      saved: false,
      webPath: 'capacitor://localhost/_capacitor_file_/profile.jpg',
    };

    await expect(mediaResultToDataUrl(result)).resolves.toMatch(/^data:image\/jpeg;base64,/);
  });

  it('recognizes native camera and gallery cancellation errors', () => {
    expect(isPhotoSelectionCancelled({ code: CameraErrorCode.TakePhotoCancelled })).toBe(true);
    expect(isPhotoSelectionCancelled({ code: CameraErrorCode.ChooseMediaCancelled })).toBe(true);
    expect(isPhotoSelectionCancelled(new Error('camera unavailable'))).toBe(false);
  });
});
