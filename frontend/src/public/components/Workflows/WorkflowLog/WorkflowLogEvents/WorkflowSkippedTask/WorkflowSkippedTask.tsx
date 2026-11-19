import React, { useCallback } from 'react';
import classnames from 'classnames';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { Header } from '../../../../UI/Typeography/Header';
import { ERoutes } from '../../../../../constants/routes';
import type { IWorkflowSkippedTaskProps, TWorkflowLogTheme } from '../../types';

import styles from './WorkflowSkippedTask.css';

export function WorkflowSkippedTask({ task, areTasksClickable, theme, onClickTask }: IWorkflowSkippedTaskProps) {
  const { formatMessage } = useIntl();

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

  const getThemeClassName = useCallback(() => {
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
          {renderTitle()}
          <p className={styles['date-started']}>
            <span className={styles['date-started__date']}>{formatMessage({ id: 'workflow.skipped-task' })}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
