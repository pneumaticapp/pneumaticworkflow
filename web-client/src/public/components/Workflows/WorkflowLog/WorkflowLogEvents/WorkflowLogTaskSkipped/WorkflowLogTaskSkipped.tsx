/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { Header } from '../../../../UI/Typeography/Header';
import { UserData } from '../../../../UserData';
import { IWorkflowLogItem } from '../../../../../types/workflow';
import { TWorkflowLogTheme } from '../../WorkflowLog';

import styles from './WorkflowLogTaskSkipped.css';

export interface IWorkflowLogTaskSkippedProps extends Pick<IWorkflowLogItem, 'task'> {
  theme: TWorkflowLogTheme;
}

const MAX_SHOW_USERS = 5;

export function WorkflowLogTaskSkipped({ task, theme }: IWorkflowLogTaskSkippedProps) {
  const { formatMessage } = useIntl();
  const renderPerformers = () => {
    if (!task?.performers) {
      return null;
    }

    const usersLeft = Math.max(task?.performers.length - MAX_SHOW_USERS, 0);

    return (
      <div className={styles['performers']}>
        {task?.performers.slice(0, MAX_SHOW_USERS).map((userId, index) => (
          <UserData userId={userId}>
            {user => {
              if (!user) {
                return null;
              }

              return (
                <Avatar
                  key={index}
                  user={user}
                  size="sm"
                  containerClassName={styles['performer']}
                  showInitials={false}
                  withTooltip
                />
              );
            }}
          </UserData>
        ))}
        {Boolean(usersLeft) && (
          <span className={styles['performers__more']}>
            +{usersLeft}
          </span>
        )}
      </div>
    );
  };

  const getThemeClassName = React.useCallback(() => {
    const themeClassNameMap: { [key in TWorkflowLogTheme]: string } = {
      beige: styles['container-beige'],
      white: styles['container-white'],
    };

    return themeClassNameMap[theme];
  }, [theme]);

  return (
    <div className={classnames(styles['container'], getThemeClassName())}>
      <div className={styles['top-area']}>
        <div className={styles['top-area__meta']}>
          <p className={styles['pre-title']}>
            {formatMessage({ id: 'workflows.step-pre-title' }, { task: task?.number })}
          </p>
          <p className={styles['skipped']}>
            {formatMessage({ id: 'workflows.log-task-skipped' })}
          </p>
        </div>

        <Header tag="h3" size="6" className={styles['task-name']}>
          {task?.name}
        </Header>
      </div>

      <div className={styles['bottom-area']}>
        {renderPerformers()}
      </div>
    </div>
  );
}
