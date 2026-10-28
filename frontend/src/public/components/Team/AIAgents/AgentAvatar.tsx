import * as React from 'react';
import classnames from 'classnames';

import { getAgentInitials } from './utils/getAgentInitials';
import type { IAgentAvatarProps } from './types';

import styles from './AgentAvatar.css';

export function AgentAvatar({ name, photo, size }: IAgentAvatarProps) {
  return (
    <div className={classnames(styles['agent-avatar'], styles[`agent-avatar_${size}`])}>
      {photo ? <img src={photo} alt="" /> : getAgentInitials(name)}
    </div>
  );
}
