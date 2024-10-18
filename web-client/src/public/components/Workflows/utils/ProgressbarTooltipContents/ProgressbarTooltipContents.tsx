import * as React from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { getLanguage } from '../../../../redux/selectors/user';
import { EWorkflowStatus, IWorkflow } from '../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../utils/dateTime';
import { DateFormat } from '../../../UI/DateFormat';
import { getDueInData } from '../../../DueIn/utils/getDueInData';

import styles from './ProgressbarTooltipContents.css';
import { reactElementToText } from '../../../../utils/reactElementToText';

interface IProgressbarTooltipContentsProps {
  workflow: IWorkflow;
}
export function ProgressbarTooltipContents({
  workflow: {
    statusUpdated,
    status,
    task: { checklistsMarked, checklistsTotal, dueDate: taskDueDate, dateStarted, delay },
    currentTask,
    tasksCount,
    dueDate,
  },
}: IProgressbarTooltipContentsProps) {
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);
  const getSnoozedText = () => {
    if (!delay) {
      return '';
    }

    return formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(delay) });
  };

  const getDueInTooltipText = (): string => {
    const dueInData = getDueInData([taskDueDate, dueDate], undefined, undefined, locale);
    if (!dueInData) {
      return '';
    }

    const { timeLeft, statusTitle } = dueInData;

    return formatMessage({ id: statusTitle }, { duration: timeLeft });
  };

  const tooltipTextMap = {
    [EWorkflowStatus.Running]: [
      formatMessage({ id: 'workflows.started' }, { date: reactElementToText(<DateFormat date={dateStarted} />) }),
      getDueInTooltipText(),
    ]
      .filter(Boolean)
      .join('\n'),
    [EWorkflowStatus.Snoozed]: getSnoozedText(),
    [EWorkflowStatus.Finished]: formatMessage(
      { id: 'workflows.finished' },
      { date: <DateFormat date={statusUpdated} /> },
    ),
    [EWorkflowStatus.Aborted]: '',
  };

  return (
    <>
      <p className={styles['tooltip-header']}>
        {formatMessage({ id: 'workflows.tooltip-header' }, { currentTask, tasksCount })}
      </p>
      <p className={styles['tooltip-content']}>{tooltipTextMap[status]}</p>
      {checklistsTotal !== 0 && (
        <>
          <p className={styles['tooltip-header']}>{formatMessage({ id: 'workflows.checklists-header' })}</p>
          <p className={styles['tooltip-content']}>
            {formatMessage(
              { id: 'workflows.checklists-counter' },
              { marked: checklistsMarked, total: checklistsTotal },
            )}
          </p>
        </>
      )}
    </>
  );
}
