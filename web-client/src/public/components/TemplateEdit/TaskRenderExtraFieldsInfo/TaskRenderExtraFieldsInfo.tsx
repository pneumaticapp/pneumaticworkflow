import React from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTask } from '../../../types/template';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';

interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();

  const ExtraFieldsText = (counter: number) => {
    let message;
    if (counter % 10 === 1 && counter % 100 !== 11) {
      message = 'tasks.task-extra-field-single';
    } else if ([2, 3, 4].includes(counter % 10) && ![12, 13, 14].includes(counter % 100)) {
      message = 'tasks.task-extra-field-plural-1';
    } else {
      message = 'tasks.task-extra-field-plural-2';
    }
    return `${counter} ${formatMessage({ id: message })}`;
  };

  return (
    fields.length > 0 && (
      <button className={styles['extra-field-label']} onClick={onClick} type="button">
        {ExtraFieldsText(fields.length)}
      </button>
    )
  );
};
