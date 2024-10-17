import React from 'react';
import { useIntl } from 'react-intl';

import { IUnsavedUser } from '../../../types/user';

import { Modal } from "..";
import { getUserFullName } from '../../../utils/users';

import styles from './Paywall.css';

export interface IPaywallProps {
  currentUser: IUnsavedUser;
  owner: IUnsavedUser;
}

export function Paywall({ owner, currentUser }: IPaywallProps) {
  if (!owner || !currentUser) return null;

  const { formatMessage } = useIntl();

  const renderMessage = () => {
    const isOwner = owner.email === currentUser.email;

    return isOwner ? (
      <p>{formatMessage({ id: 'paywall.messageOwner' })}</p>
    ) : (
      <p>
        {formatMessage(
          { id: 'paywall.messageNotOwner' },
          {name: <a href={`mailto:${owner.email}`}>{getUserFullName(owner)}</a>}
        )}
      </p>
    );
  };

  return (
    <Modal isOpen width="sm">
      <div className={styles['paywall']}>
        <h1>{formatMessage({ id: 'paywall.title' })}</h1>
        <hr />
        <p>
          <b>{formatMessage({ id: 'paywall.caption' })}</b>
        </p>
        {renderMessage()}
      </div>
    </Modal>
  );
}
