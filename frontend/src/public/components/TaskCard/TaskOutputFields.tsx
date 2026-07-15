import React from 'react';

import { ETaskStatus } from '../../redux/actions';
import { EExtraFieldMode } from '../../types/template';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { IntlMessages } from '../IntlMessages';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';
import { ITaskOutputFieldsProps } from './types';

import styles from './TaskCard.css';

export function TaskOutputFields({ accountId, outputValues, status, editField }: ITaskOutputFieldsProps) {
  const visibleOutputs = outputValues.filter((field) => !field.isHidden);

  if (!isArrayWithItems(visibleOutputs) || status === ETaskStatus.Completed) {
    return null;
  }

  return (
    <div className={styles['task-output']}>
      <p className={styles['task-output__title']}>
        <IntlMessages id="tasks.task-outputs-fill-help" />
      </p>
      {visibleOutputs.map((field) => (
        <ExtraFieldIntl
          key={field.apiName}
          field={field}
          editField={editField(field.apiName)}
          showDropdown={false}
          mode={EExtraFieldMode.ProcessRun}
          labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
          namePlaceholder={field.name}
          descriptionPlaceholder={field.description}
          wrapperClassName={styles['task-output__field']}
          accountId={accountId}
        />
      ))}
    </div>
  );
}
