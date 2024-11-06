/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { Avatar } from '../../../UI/Avatar';
import { isArrayWithItems } from '../../../../utils/helpers';
import { ETaskPerformerType, ITemplateTask, ITemplateTaskPerformer } from '../../../../types/template';
import { UserData } from '../../../UserData';

import styles from './TaskItemUsers.css';

export interface ITaskItemUsersProps {
  task: ITemplateTask;
  maxUsers?: number;
  onClick(): void;
}

const MAX_SHOW_USERS = 5;

export function TaskItemUsers({ task, maxUsers = MAX_SHOW_USERS, onClick }: ITaskItemUsersProps) {
  const { rawPerformers = [] } = task;
  if (!isArrayWithItems(rawPerformers)) {
    return null;
  }

  const usersLeft = Math.max(rawPerformers.length - maxUsers, 0);

  const renderPerformer = (performer: ITemplateTaskPerformer) => {
    const performerRenderMap: { [key in ETaskPerformerType]: (perfomer: ITemplateTaskPerformer) => React.ReactNode } = {
      [ETaskPerformerType.OutputUser]: (performer: ITemplateTaskPerformer) => {
        return <Avatar size="sm" containerClassName={styles['card-user']} isEmpty />;
      },
      [ETaskPerformerType.User]: (performer: ITemplateTaskPerformer) => {
        return (
          <UserData key={`user-${performer.sourceId}`} userId={Number(performer.sourceId)}>
            {(user) => {
              if (!user) {
                return null;
              }

              return (
                <Avatar
                  size="sm"
                  containerClassName={styles['card-user']}
                  user={user}
                  showInitials={false}
                  withTooltip
                />
              );
            }}
          </UserData>
        );
      },
      [ETaskPerformerType.UserGroup]: (performer: ITemplateTaskPerformer) => {
        return <Avatar size="sm" containerClassName={styles['card-user']} isEmpty />;
      },
      [ETaskPerformerType.WorkflowStarter]: () => {
        return <Avatar size="sm" containerClassName={styles['card-user']} isEmpty />;
      },
    };

    return performerRenderMap[performer.type](performer);
  };

  return (
    <div className={styles['card-users']} onClick={onClick}>
      {rawPerformers.map(renderPerformer)}
      {Boolean(usersLeft) && <span className={styles['card-users__more']}>+{usersLeft}</span>}
    </div>
  );
}
