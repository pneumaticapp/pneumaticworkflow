import * as React from 'react';
import { createPortal } from 'react-dom';
import classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';

import { TNotificationsListItem } from '../../types';
import { ClearIcon } from '../icons';
import { Loader } from '../UI/Loader';
import { Placeholder, SectionTitle } from '../UI';
import { isArrayWithItems } from '../../utils/helpers';
import { NotificationsListItem } from './NotificationsListItem';
import { NotificationsListPlaceholderIcon } from './NotificationsListPlaceholderIcon';
import { getNotificationListItemProps } from './getNotificationListItemProps';
import { INotificationsListProps } from './types';

import styles from './NotificationsList.css';

export type { INotificationsListProps } from './types';

export const NotificationsList = ({
  users,
  notifications,
  withPaywall,
  totalNotificationsCount,
  isClosing,
  setNotificationsListIsOpen,
  removeNotificationItem,
  fetchNotificationsAsRead,
  markNotificationsAsRead,
  loadNotificationsList,
}: INotificationsListProps) => {
  const { formatMessage } = useIntl();

  React.useEffect(() => {
    fetchNotificationsAsRead();

    return () => {
      markNotificationsAsRead();
    };
  }, []);

  React.useEffect(() => {
    fetchNotificationsAsRead();
  }, [notifications.length]);

  const handleCloseNotifications = () => {
    setNotificationsListIsOpen(false);
  };

  const renderListItem = (notification: TNotificationsListItem) => {
    const notificationsProps = getNotificationListItemProps({
      notification,
      users,
      formatMessage,
      removeNotificationItem,
    });

    if (!notificationsProps) {
      return null;
    }

    return (
      <NotificationsListItem
        key={`NotificationsListItem${notification.id}`}
        {...notificationsProps}
        onClick={handleCloseNotifications}
      />
    );
  };

  const renderList = () => {
    if (!isArrayWithItems(notifications)) {
      return (
        <Placeholder
          title={formatMessage({ id: 'notifications.empty-placeholder-title' })}
          description={formatMessage({ id: 'notifications.empty-placeholder-description' })}
          Icon={NotificationsListPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['empty-list-placeholder']}
        />
      );
    }

    const handleNext = () => loadNotificationsList({ offset: notifications.length });

    return (
      <div className={styles['notifications-list']} id="notifications-list">
        <InfiniteScroll
          dataLength={notifications.length}
          next={handleNext}
          loader={<Loader isLoading />}
          hasMore={notifications.length < totalNotificationsCount}
          scrollableTarget="notifications-list"
        >
          {notifications.map(renderListItem)}
        </InfiniteScroll>
      </div>
    );
  };

  const renderNotifications = () => {
    return (
      <OutsideClickHandler onOutsideClick={handleCloseNotifications}>
        <div
          className={classnames(
            styles['container'],
            'no-print',
            !isClosing ? styles['container_opened'] : styles['container_closed'],
            withPaywall && styles['container_with-paywall'],
          )}
        >
          <div className={styles['header']}>
            <SectionTitle>{formatMessage({ id: 'notifications.title' })}</SectionTitle>

            <button
              onClick={handleCloseNotifications}
              type="button"
              className={styles['close-button']}
              aria-label="Close modal"
              data-test-id="close"
            >
              <ClearIcon />
            </button>
          </div>

          {renderList()}
        </div>
      </OutsideClickHandler>
    );
  };

  return createPortal(renderNotifications(), document.body);
};
