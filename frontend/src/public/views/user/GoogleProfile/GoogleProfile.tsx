import * as React from 'react';

import { Avatar } from '../../../components/UI/Avatar';
import { EUserStatus } from '../../../types/user';

import styles from './GoogleProfile.css';

export interface IGoogleProfileProps {
  photo?: string;
  firstName?: string;
  lastName?: string;
  email?: string;
}

export function GoogleProfile({ photo = '', firstName = '', lastName = '', email = '' }: IGoogleProfileProps) {
  if (!email) {
    return null;
  }

  return (
    <div className="d-flex mb-4">
      <div className="d-flex align-items-center mr-3">
        <Avatar
          className={styles['avatar']}
          user={{
            firstName,
            lastName,
            email,
            photo,
            status: EUserStatus.Registration,
          }}
        />
      </div>
      <div className="d-flex flex-column">
        <span>
          {firstName} {lastName}
        </span>
        <span>{email}</span>
      </div>
    </div>
  );
}
