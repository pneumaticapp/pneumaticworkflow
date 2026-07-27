import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { IFieldsetBindingClient } from '../../../types/template';
import { getTriplePlural } from '../../../utils/helpers';
import { ITaskRenderExtraFieldsInfoProps } from './types';
import styles from '../ExtraFields/utils/ExtraFieldsLabels/ExtraFieldsLabels.css';

function countFieldsetOutputFields(fieldsets: IFieldsetBindingClient[] | undefined): number {
  if (!fieldsets?.length) {
    return 0;
  }

  return fieldsets.reduce((acc, fieldset) => acc + fieldset.fields.length, 0);
}

export const TaskRenderExtraFieldsInfo = ({ task: { fields, fieldsets }, onClick }: ITaskRenderExtraFieldsInfoProps) => {
  const { formatMessage } = useIntl();
  const counter = useMemo(
    () => fields.length + countFieldsetOutputFields(fieldsets),
    [fieldsets, fields.length],
  );

  const extraFieldsText = getTriplePlural({
    counter,
    forms: ['tasks.task-extra-field-single', 'tasks.task-extra-field-plural-1', 'tasks.task-extra-field-plural-2'],
    formatMessage,
  });

  if (!counter) {
    return null;
  }

  return (
    <button className={styles['extra-field-label']} onClick={onClick} type="button">
      {extraFieldsText}
    </button>
  );
};
