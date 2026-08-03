import React from 'react';
import { IntlShape } from 'react-intl';

import { getTaskDetailRoute, getWorkflowDetailedRoute } from '../../utils/routes';
import { Avatar } from '../UI/Avatar';
import { getUserFullName } from '../../utils/users';
import { TNotificationsListItem } from '../../types';
import {
  AlarmCrossedIcon,
  AlarmIcon,
  CommentInfoIcon,
  NotUrgentIcon,
  PneumaticAvatarIcon,
  TaskCompleteIcon,
  UrgentColorIcon,
} from '../icons';
import { RichText } from '../RichText';
import { TUserListItem } from '../../types/user';
import { getUserById } from '../UserData/utils/getUserById';
import { DateFormat } from '../UI/DateFormat/container';
import { reactElementToText } from '../../utils/reactElementToText';
import { INotificationsListItemProps } from './NotificationsListItem';

import styles from './NotificationsList.css';

interface IGetNotificationListItemPropsConfig {
  notification: TNotificationsListItem;
  users: TUserListItem[];
  formatMessage: IntlShape['formatMessage'];
  removeNotificationItem(value: { notificationId: number }): void;
}

export function getNotificationListItemProps({
  notification,
  users,
  formatMessage,
  removeNotificationItem,
}: IGetNotificationListItemPropsConfig): Omit<INotificationsListItemProps, 'onClick'> | null {
  const commonProps = {
    date: reactElementToText(<DateFormat date={notification.datetime} />),
    status: notification.status,
    removeNotificationItem: () => removeNotificationItem({ notificationId: notification.id }),
  };

  switch (notification.type) {
    case 'complete_task': {
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
        icon: <TaskCompleteIcon size="sm" />,
        title: getUserFullName(author),
        subtitle: notification.workflow.name,
        text: formatMessage(
          { id: 'workflows.log-complete' },
          { taskName: <span className={styles['notification-item__completed-task-name']}>{notification.task.name}</span> },
        ),
        link: getTaskDetailRoute(notification.task.id),
      };
    }
    case 'complete_workflow':
      return {
        ...commonProps,
        avatar: <PneumaticAvatarIcon className={styles['avatar__container']} />,
        icon: <TaskCompleteIcon size="sm" />,
        title: formatMessage({ id: 'general.pneumatic' }),
        subtitle: notification.workflow.name,
        text: formatMessage({ id: 'notifications.workflow-completed' }),
        link: getWorkflowDetailedRoute(notification.workflow.id),
      };
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
    case 'comment':
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
    case 'overdue_task':
      return {
        ...commonProps,
        avatar: <PneumaticAvatarIcon className={styles['avatar__container']} />,
        icon: <AlarmIcon fill="#F44336" />,
        title: formatMessage({ id: 'general.pneumatic' }),
        subtitle: notification.workflow.name,
        text: formatMessage({ id: 'notifications.overdue' }, { task: <strong>{notification.task.name}</strong> }),
        link: getTaskDetailRoute(notification.task.id),
      };
    case 'system':
      return {
        ...commonProps,
        avatar: <PneumaticAvatarIcon className={styles['avatar__container']} />,
        icon: <CommentInfoIcon />,
        title: formatMessage({ id: 'general.pneumatic' }),
        text: <RichText text={notification.text} />,
      };
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
}
