import React from 'react';
import { useIntl } from 'react-intl';
import { ITemplateTask } from '../../../types/template';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';
import { getTriplePlural } from '../../../utils/helpers';

interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTask;
  onClick: () => void;
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();

  const extraFieldsText = getTriplePlural({
    counter: fields.length,
    forms: ['tasks.task-extra-field-single', 'tasks.task-extra-field-plural-1', 'tasks.task-extra-field-plural-2'],
    formatMessage,
  });

  return (
    fields.length > 0 && (
      <button className={styles['extra-field-label']} onClick={onClick} type="button">
        {extraFieldsText}
      </button>
    )
  );
};
