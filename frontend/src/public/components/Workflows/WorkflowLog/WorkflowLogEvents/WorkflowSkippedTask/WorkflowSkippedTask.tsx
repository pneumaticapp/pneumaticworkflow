/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { Header } from '../../../../UI/Typeography/Header';
import { ERoutes } from '../../../../../constants/routes';
import { IWorkflowLogItem } from '../../../../../types/workflow';
import { TWorkflowLogTheme } from '../../WorkflowLog';

import styles from './WorkflowSkippedTask.css';

export interface IWorkflowSkippedTaskProps extends Pick<IWorkflowLogItem, 'task'> {
  areTasksClickable?: boolean;
  theme: TWorkflowLogTheme;
  onClickTask?(): void;
}

export function WorkflowSkippedTask({
  task,
  areTasksClickable,
  theme,
  onClickTask,
}: IWorkflowSkippedTaskProps) {
  const { formatMessage } = useIntl();

  const renderTitle = () => {
    const redirectUrl = ERoutes.TaskDetail.replace(':id', String(task?.id));
    const title = areTasksClickable ? (
      <Link
        to={redirectUrl}
        onClick={onClickTask}
      >
        {task?.name}
      </Link>
    ) : task?.name;

    return (
      <Header tag="h3" size="6" className={styles['task-name']}>
        {title}
      </Header>
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
            <span className={styles['date-started__date']}>
              {formatMessage({ id: 'workflow.skipped-task' })}
            </span>
          </p>
        </div>

        {renderTitle()}
      </div>
    </div>
  );
}
