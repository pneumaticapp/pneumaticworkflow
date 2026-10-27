const AVATAR_SIZE = 256;
const SPOTS_COUNT = 3;

const getRandom = (min: number, max: number) => min + Math.random() * (max - min);
const getColor = (hue: number) => `hsl(${Math.round(hue) % 360}, 75%, 62%)`;

export async function generateAgentAvatar(): Promise<File | null> {
  const canvas = document.createElement('canvas');
  canvas.width = AVATAR_SIZE;
  canvas.height = AVATAR_SIZE;
  const context = canvas.getContext('2d');
  if (!context) return null;

  const hue = getRandom(0, 360);
  const gradient = context.createLinearGradient(0, 0, AVATAR_SIZE, AVATAR_SIZE);
  gradient.addColorStop(0, getColor(hue));
  gradient.addColorStop(1, getColor(hue + 60));
  context.fillStyle = gradient;
  context.fillRect(0, 0, AVATAR_SIZE, AVATAR_SIZE);

  context.globalAlpha = 0.6;
  context.filter = `blur(${AVATAR_SIZE / 10}px)`;
  Array.from({ length: SPOTS_COUNT }).forEach(() => {
    context.fillStyle = getColor(hue + 360 + getRandom(-90, 90));
    context.beginPath();
    context.arc(
      getRandom(0, AVATAR_SIZE),
      getRandom(0, AVATAR_SIZE),
      getRandom(0.2, 0.5) * AVATAR_SIZE,
      0,
      Math.PI * 2,
    );
    context.fill();
  });

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, 'image/png');
  });

  return blob ? new File([blob], 'ai-agent-avatar.png', { type: 'image/png' }) : null;
}
