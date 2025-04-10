import React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { formatDuration, formatDurationMonths, getZeroDuration } from '../../../utils/dateTime';
import { ClockIcon } from '../../icons';
import { ITemplateTask } from '../../../types/template';

import styles from '../TemplateEdit.css';

interface ITaskRenderDueInProps {
  task: ITemplateTask;
  onClick: () => void;
  isInTaskForm?: boolean;
}

export const TaskRenderDueIn = ({
  task: {
    rawDueDate: { duration, durationMonths },
  },
  onClick,
  isInTaskForm,
}: ITaskRenderDueInProps) => {
  const { formatMessage } = useIntl();
  const DUE_IN_TEMPLATE = 'D[d] H[h] m[m]';

  if (duration === null && durationMonths === null) {
    return null;
  }

  const durationFormat = formatDuration(duration, DUE_IN_TEMPLATE);
  const durationMonthsFormat = formatDurationMonths(durationMonths);
  const totalDuration = getZeroDuration(duration, durationMonths) || `${durationMonthsFormat} ${durationFormat}`;

  return (
    <span
      className={classNames(styles['task-preview-due-in'], !isInTaskForm && styles['task-preview-due-in_mb-16'])}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClick();
        }
      }}
    >
      {formatMessage({ id: 'tasks.task-due-date-duration' }, { duration: totalDuration })}
      <ClockIcon className={styles['task-preview-due-in__icon']} />
    </span>
  );
};
