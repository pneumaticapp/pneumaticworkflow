import { Avatar, Style } from '@dicebear/core';
import lorelei from '@dicebear/styles/lorelei.json';

import { createUniqueId } from '../../../../utils/createId';

const loreleiStyle = new Style(lorelei);

export const generateAgentAvatar = (seed = createUniqueId('ai-agent-xxxxxxxx')): File => {
  const svg = new Avatar(loreleiStyle, { seed }).toString();

  return new File([svg], 'ai-agent-avatar.svg', { type: 'image/svg+xml' });
};
