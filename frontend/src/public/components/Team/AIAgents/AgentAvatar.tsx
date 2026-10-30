import React from 'react';
import classnames from 'classnames';

import { getBackgroundColor } from '../../UI/Avatar';
import { getAgentInitials } from './utils/getAgentInitials';
import type { IAgentAvatarProps } from './types';

import styles from './AgentAvatar.css';

export function AgentAvatar({ name, photo, size }: IAgentAvatarProps) {
  const className = classnames(styles['agent-avatar'], styles[`agent-avatar_${size}`]);

  if (photo) {
    return (
      <div className={className}>
        <img src={photo} alt="" />
      </div>
    );
  }

  const trimmedName = name.trim();

  if (!trimmedName) {
    return <div className={classnames(className, styles['agent-avatar_empty'])} />;
  }

  return (
    <div className={className} style={{ backgroundColor: getBackgroundColor(trimmedName) }}>
      {getAgentInitials(trimmedName)}
    </div>
  );
}
