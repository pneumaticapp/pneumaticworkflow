import React from 'react';
import { useIntl } from 'react-intl';
import { ITaskRenderExtraFieldsInfoProps } from './types';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';
import { getTriplePlural } from '../../../utils/helpers';

export const TaskRenderExtraFieldsInfo = ({ task: { fields }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();

  const extraFieldsText = getTriplePlural({
    counter: fields.length,
    forms: ['tasks.task-extra-field-single', 'tasks.task-extra-field-plural-1', 'tasks.task-extra-field-plural-2'],
    formatMessage,
  });

  if (!fields.length) {
    return null;
  }

  return (
    <button className={styles['extra-field-label']} onClick={onClick} type="button">
      {extraFieldsText}
    </button>
  );
};
