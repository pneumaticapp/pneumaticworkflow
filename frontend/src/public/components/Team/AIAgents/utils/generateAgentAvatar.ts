import { Avatar, Style } from '@dicebear/core';
import lorelei from '@dicebear/styles/lorelei.json';

import { createUniqueId } from '../../../../utils/createId';

const AVATAR_SIZE = 256;
const BACKGROUND_COLOR_VARIABLE = '--pneumatic-color-beige';

const loreleiStyle = new Style(lorelei);

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = reject;
    image.src = src;
  });

// The file service stores SVG as an opaque binary (XSS guard), so the avatar is uploaded as PNG.
export const generateAgentAvatar = async (seed = createUniqueId('ai-agent-xxxxxxxx')): Promise<File | null> => {
  const canvas = document.createElement('canvas');
  canvas.width = AVATAR_SIZE;
  canvas.height = AVATAR_SIZE;
  const context = canvas.getContext('2d');
  if (!context) return null;

  const image = await loadImage(new Avatar(loreleiStyle, { seed, size: AVATAR_SIZE }).toDataUri());

  context.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(BACKGROUND_COLOR_VARIABLE).trim();
  context.fillRect(0, 0, AVATAR_SIZE, AVATAR_SIZE);
  context.drawImage(image, 0, 0, AVATAR_SIZE, AVATAR_SIZE);

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, 'image/png');
  });

  return blob ? new File([blob], 'ai-agent-avatar.png', { type: 'image/png' }) : null;
};
