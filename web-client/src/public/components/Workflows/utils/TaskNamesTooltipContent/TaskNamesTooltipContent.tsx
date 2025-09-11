import React from 'react';
import { useIntl } from 'react-intl';

import styles from './TaskNamesTooltipContent.css';

export const TaskNamesTooltipContent = (taskNames: Record<string, string>) => {
  const { formatMessage } = useIntl();

  return Object.entries(taskNames).map(([apiName, name], index) => (
    <div key={apiName}>
      <div className={styles['card-tooltip-task-number']}>
        {`${formatMessage({ id: 'workflows.tasks' })} ${index + 1}`}
      </div>
      <div>{name}</div>
    </div>
  ));
};
