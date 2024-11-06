/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useSelector } from 'react-redux';
import { getLanguage } from '../../../../../redux/selectors/user';
import classnames from 'classnames';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { Avatar } from '../../../../UI/Avatar';
import { Header } from '../../../../UI/Typeography/Header';
import { DateFormat } from '../../../../UI/DateFormat';
import { ERoutes } from '../../../../../constants/routes';
import { UserData } from '../../../../UserData';
import { getLastTaskLogEventId } from './utils/getLastTaskLogEventId';
import { ClockIcon } from '../../../../icons';
import { getDueInData } from '../../../../DueIn/utils/getDueInData';
import { EWorkflowsLogSorting, TWorkflowTask, IWorkflowLogItem } from '../../../../../types/workflow';
import { TWorkflowLogTheme } from '../../WorkflowLog';

import styles from './WorkflowLogTaskStart.css';

const MAX_SHOW_USERS = 5;

export interface IWorkflowLogTaskStartProps extends Pick<IWorkflowLogItem, 'task' | 'created' | 'id'> {
  logItems: IWorkflowLogItem[];
  sorting: EWorkflowsLogSorting;
  currentTask?: TWorkflowTask;
  areTasksClickable?: boolean;
  theme: TWorkflowLogTheme;
  onClickTask?(): void;
}

export function WorkflowLogTaskStart({
  id,
  logItems,
  sorting,
  task,
  created,
  currentTask,
  areTasksClickable,
  theme,
  onClickTask,
}: IWorkflowLogTaskStartProps) {
  const dueDate = (id === getLastTaskLogEventId(logItems, sorting) && currentTask?.dueDate) || null;
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);
  const renderResponsiblesAvatars = () => {
    if (!task?.performers) {
      return null;
    }

    const usersLeft = Math.max(task?.performers.length - MAX_SHOW_USERS, 0);

    return (
      <div className={styles['start-responsibles']}>
        {task?.performers.slice(0, MAX_SHOW_USERS).map((userId, index) => (
          <UserData key={index} userId={userId}>
            {(user) => {
              if (!user) {
                return null;
              }

              return (
                <Avatar
                  user={user}
                  size="sm"
                  containerClassName={styles['start-responsible']}
                  showInitials={false}
                  withTooltip
                />
              );
            }}
          </UserData>
        ))}
        {Boolean(usersLeft) && <span className={styles['start-responsibles__more']}>+{usersLeft}</span>}
      </div>
    );
  };

  const renderTitle = () => {
    const redirectUrl = ERoutes.TaskDetail.replace(':id', String(task?.id));
    const title = areTasksClickable ? (
      <Link to={redirectUrl} onClick={onClickTask}>
        {task?.name}
      </Link>
    ) : (
      task?.name
    );

    return (
      <Header tag="h3" size="6" className={styles['task-name']}>
        {title}
      </Header>
    );
  };

  const renderDueIn = () => {
    const dueInData = getDueInData([dueDate], undefined, undefined, locale);
    if (!dueInData) {
      return null;
    }

    const { timeLeft, statusTitle, isOverdue } = dueInData;

    return (
      <div className={classnames(styles['due-in'], isOverdue && styles['due-in_overdue'])}>
        <p className={styles['due-in__inner']}>
          <span className={styles['due-in__text']}>{formatMessage({ id: statusTitle }, { duration: timeLeft })}</span>
          <ClockIcon className={styles['due-in__icon']} />
        </p>
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
            {formatMessage({ id: 'workflows.log-task-started-pre-title' }, { task: task?.number })}
          </p>
          <p className={styles['date-started']}>
            {formatMessage({ id: 'workflows.log-task-started' })}
            &nbsp;
            <span className={styles['date-started__date']}>
              <DateFormat date={created} />
            </span>
          </p>
        </div>

        {renderTitle()}
      </div>

      <div className={styles['bottom-area']}>
        {renderResponsiblesAvatars()}
        {renderDueIn()}
      </div>
    </div>
  );
}
