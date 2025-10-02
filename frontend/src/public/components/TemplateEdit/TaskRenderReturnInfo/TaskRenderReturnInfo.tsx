import React from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTask } from '../../../types/template';
import styles from '../TemplateEdit.css';

interface ITaskRenderReturnInfoProps {
  task: ITemplateTask;
  onClick: () => void;
}

export const TaskRenderReturnInfo = ({ task: { revertTask }, onClick }: ITaskRenderReturnInfoProps) => {
  const { formatMessage } = useIntl();

  return (
    revertTask && (
      <span
        className={styles['task-view__return-info']}
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onClick();
          }
        }}
      >
        {formatMessage({ id: 'templates.return-to.minimize' })}
      </span>
    )
  );
};
