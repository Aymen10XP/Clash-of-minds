import { Haptics, NotificationType } from '@capacitor/haptics';

type ResultKind = 'correct' | 'wrong';

const playTone = (kind: ResultKind) => {
  const LegacyAudioContext = (
    window as typeof window & { webkitAudioContext?: typeof AudioContext }
  ).webkitAudioContext;
  const AudioContextConstructor = window.AudioContext ?? LegacyAudioContext;
  if (!AudioContextConstructor) return;

  const context = new AudioContextConstructor();
  const gain = context.createGain();
  const notes = kind === 'correct' ? [523.25, 659.25, 783.99] : [220, 164.81];
  const now = context.currentTime;
  gain.connect(context.destination);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.16, now + 0.012);

  notes.forEach((frequency, index) => {
    const oscillator = context.createOscillator();
    oscillator.type = kind === 'correct' ? 'sine' : 'sawtooth';
    oscillator.frequency.setValueAtTime(frequency, now + index * 0.09);
    oscillator.connect(gain);
    oscillator.start(now + index * 0.09);
    oscillator.stop(now + index * 0.09 + 0.14);
  });

  const duration = kind === 'correct' ? 0.38 : 0.32;
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
  window.setTimeout(() => void context.close(), (duration + 0.1) * 1000);
};

export const playAnswerFeedback = (kind: ResultKind) => {
  playTone(kind);
  void Haptics.notification({
    type: kind === 'correct' ? NotificationType.Success : NotificationType.Error,
  }).catch(() => undefined);
};
