import * as React from 'react';
import { createPortal } from 'react-dom';
import * as classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';

import { getTaskDetailRoute } from '../../utils/routes';
import { Avatar } from '../UI/Avatar';
import { getUserFullName } from '../../utils/users';
import { TNotificationsListItem } from '../../types';
import {
  ClearIcon,
  CommentInfoIcon,
  PneumaticAvatarIcon,
  UrgentColorIcon,
  NotUrgentIcon,
  AlarmIcon,
  AlarmCrossedIcon,
} from '../icons';
import { Loader } from '../UI/Loader';
import { RichText } from '../RichText';
import { TUserListItem } from '../../types/user';
import { getUserById } from '../UserData/utils/getUserById';
import { Placeholder, SectionTitle } from '../UI';
import { IChangeNotificationsListPayload, ILoadNotificationsPayload } from '../../redux/notifications/actions';
import { isArrayWithItems } from '../../utils/helpers';
import { NotificationsListItem, INotificationsListItemProps } from './NotificationsListItem';
import { NotificationsListPlaceholderIcon } from './NotificationsListPlaceholderIcon';
import { DateFormat } from '../UI/DateFormat';
import { reactElementToText } from '../../utils/reactElementToText';

import styles from './NotificationsList.css';

export interface INotificationsListProps {
  users: TUserListItem[];
  notifications: TNotificationsListItem[];
  isLoading: boolean;
  withPaywall: boolean;
  totalNotificationsCount: number;
  isClosing: boolean;
  setNotificationsListIsOpen(payload: boolean): void;
  removeNotificationItem(value: { notificationId: number }): void;
  changeNotificationsList(notifications: IChangeNotificationsListPayload): void;
  fetchNotificationsAsRead(): void;
  markNotificationsAsRead(): void;
  loadNotificationsList(payload?: ILoadNotificationsPayload): void;
}

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
    const getNotificationsProps = (): Omit<INotificationsListItemProps, 'onClick'> | null => {
      const commonProps = {
        date: reactElementToText(<DateFormat date={notification.datetime} />),
        status: notification.status,
        removeNotificationItem: () => removeNotificationItem({ notificationId: notification.id }),
      };

      switch (notification.type) {
        case 'reaction': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <CommentInfoIcon />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: notification.text,
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'urgent': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <UrgentColorIcon />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: formatMessage({ id: 'notifications.task-was-marked' }),
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'not_urgent': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <NotUrgentIcon fill="#B9B9B8" />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: formatMessage({ id: 'notifications.workflow-no-loner-urgent' }),
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'comment': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <CommentInfoIcon />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: <RichText text={notification.text} />,
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'mention': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <CommentInfoIcon />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: <RichText text={notification.text} />,
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'overdue_task': {
          return {
            ...commonProps,
            avatar: <PneumaticAvatarIcon className={styles['avatar__container']} />,
            icon: <AlarmIcon fill="#F44336" />,
            title: formatMessage({ id: 'general.pneumatic' }),
            subtitle: notification.workflow.name,
            text: formatMessage({ id: 'notifications.overdue' }, { task: <strong>{notification.task.name}</strong> }),
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'system': {
          return {
            ...commonProps,
            avatar: <PneumaticAvatarIcon className={styles['avatar__container']} />,
            icon: <CommentInfoIcon />,
            title: formatMessage({ id: 'general.pneumatic' }),
            text: <RichText text={notification.text} />,
          };
        }
        case 'snooze_workflow': {
          const author = getUserById(users, notification.author);
          const snoozedUntilDate = <DateFormat date={notification.task.delay?.estimatedEndDate} />;

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <AlarmIcon fill="#F44336" />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: formatMessage({ id: 'notifications.snoozed' }, { date: snoozedUntilDate }),
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        case 'resume_workflow': {
          const author = getUserById(users, notification.author);

          return {
            ...commonProps,
            avatar: author && (
              <Avatar
                user={author}
                className={styles['avatar__image']}
                containerClassName={styles['avatar__container']}
              />
            ),
            icon: <AlarmCrossedIcon fill="#4CAF50" />,
            title: getUserFullName(author),
            subtitle: notification.workflow.name,
            text: formatMessage({ id: 'notifications.resumed' }),
            link: getTaskDetailRoute(notification.task.id),
          };
        }
        default:
          return null;
      }
    };

    const notificationsProps = getNotificationsProps();

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
