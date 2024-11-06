/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { useIntl } from 'react-intl';
import { TrashIcon } from '../icons';
import { NavLink } from '../NavLink';
import { TNotificationsListItemStatus } from '../../types';

import styles from './NotificationsList.css';

export interface INotificationsListItemProps {
  avatar: React.ReactNode;
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  date: string;
  text: React.ReactNode;
  link?: string;
  status: TNotificationsListItemStatus;
  removeNotificationItem(): void;
  onClick(): void;
}

export function NotificationsListItem({
  avatar,
  icon,
  title,
  subtitle,
  date,
  text,
  link,
  status,
  removeNotificationItem,
  onClick,
}: INotificationsListItemProps) {
  const { formatMessage } = useIntl();

  const handleRemoveNotification = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    event.preventDefault();
    event.stopPropagation();

    removeNotificationItem();
  };

  const renderItemContent = () => {
    return (
      <>
        <div className={styles['notification-item__avatar']}>{avatar}</div>
        <p className={styles['notification-item-title']}>
          <span className={styles['notification-item-title__text']}>{title}</span>
          <span className={styles['notification-item-title__icon']}>{icon}</span>
          <span className={styles['notification-item-title__date']}>{date}</span>
        </p>

        {subtitle && <p className={styles['notification-item__subtitle']}>{subtitle}</p>}

        <div className={styles['notification-item__text']}>{text}</div>

        <button
          type="button"
          aria-label={formatMessage({ id: 'notifications.remove-item' })}
          onClick={handleRemoveNotification}
          className={styles['notification-item__remove']}
        >
          <TrashIcon />
        </button>
      </>
    );
  };

  const containerClassName = classnames(
    styles['notification-item'],
    status === 'new' && styles['notification-item_new'],
  );

  if (link) {
    return (
      <NavLink to={link} onClick={onClick} className={containerClassName}>
        {renderItemContent()}
      </NavLink>
    );
  }

  return (
    <div onClick={onClick} className={containerClassName}>
      {renderItemContent()}
    </div>
  );
}
