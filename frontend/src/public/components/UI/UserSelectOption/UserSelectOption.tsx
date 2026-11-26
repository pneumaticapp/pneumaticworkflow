import React from 'react';
import { Avatar } from '../Avatar';
import type { IUserSelectOptionProps } from './types';

import styles from './UserSelectOption.css';

export const UserSelectOption = ({ user, name }: IUserSelectOptionProps) => (
  <div className={styles['user-select-option']}>
    <Avatar user={user} size="sm" />
    <span className={styles['user-select-option__name']}>{name}</span>
  </div>
);
