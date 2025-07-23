import * as React from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { getLanguage } from '../../../../redux/selectors/user';
import { EWorkflowStatus, IWorkflowClient } from '../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../utils/dateTime';
import { DateFormat } from '../../../UI/DateFormat';
import { getDueInData } from '../../../DueIn/utils/getDueInData';

import styles from './ProgressbarTooltipContents.css';

interface IProgressbarTooltipContentsProps {
  workflow: IWorkflowClient;
}
export function ProgressbarTooltipContents({
  workflow: {
    dateCompleted,
    status,
    lastActiveCurrentTask,
    tasksCountWithoutSkipped,
    dueDate,
    minDelay,
    dateCreated,
    oldestDeadline,
  },
}: IProgressbarTooltipContentsProps) {
  const { formatMessage } = useIntl();
  const locale = useSelector(getLanguage);
  const getSnoozedText = () => {
    if (!minDelay) {
      return '';
    }

    return formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(minDelay) });
  };

  const getDueInTooltipText = (): string => {
    const dueInData = getDueInData([oldestDeadline, dueDate], undefined, undefined, locale);
    if (!dueInData) {
      return '';
    }

    const { timeLeft, statusTitle } = dueInData;

    return formatMessage({ id: statusTitle }, { duration: timeLeft });
  };

  const getRunningTooltipText = () => {
    const startedProcessText = formatMessage({ id: 'workflows.started' }, { date: <DateFormat date={dateCreated} /> });
    const dueInText = getDueInTooltipText();

    return dueInText ? (
      <>
        {startedProcessText}
        <br />
        {dueInText}
      </>
    ) : (
      startedProcessText
    );
  };

  const tooltipTextMap = {
    [EWorkflowStatus.Running]: getRunningTooltipText(),
    [EWorkflowStatus.Snoozed]: getSnoozedText(),
    [EWorkflowStatus.Finished]:
      dateCompleted && formatMessage({ id: 'workflows.finished' }, { date: <DateFormat date={dateCompleted} /> }),
    [EWorkflowStatus.Aborted]: '',
  };

  return (
    <>
      <p className={styles['tooltip-header']}>
        {formatMessage({ id: 'workflows.tooltip-header' }, { lastActiveCurrentTask, tasksCountWithoutSkipped })}
      </p>
      <p className={styles['tooltip-content']}>{tooltipTextMap[status]}</p>
    </>
  );
}
