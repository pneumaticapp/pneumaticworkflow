import React from 'react';

import { ETaskStatus } from '../../redux/actions';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { IntlMessages } from '../IntlMessages';
import { MergedOutputList } from '../MergedOutputList';
import { ITaskOutputFieldsProps } from './types';

import styles from './TaskCard.css';

export function TaskOutputFields({
  accountId,
  editField,
  editFieldsetField,
  fieldsetOutputValues,
  isDisabled,
  onUploadStateChange,
  outputValues,
  status,
  taskId,
}: ITaskOutputFieldsProps) {
  const visibleOutputs = outputValues.filter((field) => !field.isHidden);

  if ((!isArrayWithItems(visibleOutputs) && !isArrayWithItems(fieldsetOutputValues)) || status === ETaskStatus.Completed) {
    return null;
  }

  return (
    <div className={styles['task-output']}>
      <p className={styles['task-output__title']}>
        <IntlMessages id="tasks.task-outputs-fill-help" />
      </p>
      <MergedOutputList
        key={taskId}
        fields={visibleOutputs}
        fieldsets={fieldsetOutputValues}
        onEditField={editField}
        onEditFieldsetField={editFieldsetField}
        labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
        fieldClassName={styles['task-output__field']}
        accountId={accountId}
        isDisabled={isDisabled}
        onUploadStateChange={onUploadStateChange}
      />
    </div>
  );
}
