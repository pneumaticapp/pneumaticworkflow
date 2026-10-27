const AVATAR_SIZE = 256;
const FALLBACK_INITIALS = 'AI';

const getRandomBackgroundColor = () => `hsl(${Math.floor(Math.random() * 360)}, 60%, 60%)`;

export async function generateAgentAvatar(initials: string): Promise<File | null> {
  const canvas = document.createElement('canvas');
  canvas.width = AVATAR_SIZE;
  canvas.height = AVATAR_SIZE;
  const context = canvas.getContext('2d');
  if (!context) return null;

  await document.fonts?.ready;

  context.fillStyle = getRandomBackgroundColor();
  context.fillRect(0, 0, AVATAR_SIZE, AVATAR_SIZE);
  context.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--pneumatic-color-white').trim();
  context.font = `bold ${AVATAR_SIZE * 0.4}px Nunito, sans-serif`;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(initials || FALLBACK_INITIALS, AVATAR_SIZE / 2, AVATAR_SIZE / 2);

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, 'image/png');
  });

  return blob ? new File([blob], 'ai-agent-avatar.png', { type: 'image/png' }) : null;
}
