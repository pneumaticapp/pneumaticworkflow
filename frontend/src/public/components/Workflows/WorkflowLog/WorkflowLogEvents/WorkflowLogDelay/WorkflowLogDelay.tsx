import React, { useCallback } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { IWorkflowLogItem, IWorkflowLogTask, EWorkflowLogEvent } from '../../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../../utils/dateTime';
import { Header } from '../../../../UI/Typeography/Header';
import { TWorkflowLogTheme } from '../../WorkflowLog';

import styles from './WorkflowLogDelay.css';

export interface IWorkflowLogDelayProps extends Pick<IWorkflowLogItem, 'delay'> {
  theme: TWorkflowLogTheme;
  task?: IWorkflowLogTask | null;
  type?: EWorkflowLogEvent;
}

export function WorkflowLogDelay({ delay, task, theme, type }: IWorkflowLogDelayProps) {
  if (!delay) {
    return null;
  }

  const getThemeClassName = useCallback(() => {
    const themeClassNameMap: { [key in TWorkflowLogTheme]: string } = {
      beige: styles['container-beige'],
      white: styles['container-white'],
    };

    return themeClassNameMap[theme];
  }, [theme]);

  const { formatMessage } = useIntl();

  return (
    <div className={classnames(styles['container'], getThemeClassName())}>
      <Header size="6" tag="p" className={styles['text']}>
        {type === EWorkflowLogEvent.TaskSnoozed
          ? formatMessage({ id: 'task.log-delay' }, { taskName: task?.name, date: getSnoozedUntilDate(delay) })
          : formatMessage({ id: 'task.log-delay-workflow' }, { date: getSnoozedUntilDate(delay) })}
      </Header>
    </div>
  );
}
