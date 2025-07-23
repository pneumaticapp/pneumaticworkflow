import React from 'react';
import { useIntl } from 'react-intl';

import styles from './TaskNamesTooltipContent.css';

export const TaskNamesTooltipContent = (taskNames: string[]) => {
  const { formatMessage } = useIntl();

  return taskNames.map((name, index) => (
    <div key={name}>
      <div className={styles['card-tooltip-task-number']}>
        {`${formatMessage({ id: 'workflows.tasks' })} ${index + 1}`}
      </div>
      <div>{name}</div>
    </div>
  ));
};
