import React from 'react';
import { useIntl } from 'react-intl';

import { ITaskFormHeaderProps } from './types';
import { InputWithVariables } from '../InputWithVariables';
import { TaskDescriptionEditor } from './TaskDescriptionEditor';
import { getSingleLineVariables } from './utils/getTaskVariables';
import { useTaskForm } from './useTaskForm';

import styles from '../TemplateEdit.css';

export function TaskFormHeader({
  accountId,
  listSystemVariables,
  templateVariables,
}: ITaskFormHeaderProps) {
  const { formatMessage } = useIntl();
  const { task, updateField } = useTaskForm();

  return (
    <div className={styles['task-fields-wrapper']}>
      <InputWithVariables
        placeholder={formatMessage({ id: 'tasks.task-task-name-placeholder' })}
        listVariables={getSingleLineVariables(listSystemVariables)}
        templateVariables={templateVariables}
        showInsertButton
        value={task.name || ''}
        onChange={(value: string) => {
          updateField('name')(value);

          return Promise.resolve(value);
        }}
        className={styles['task-name-field']}
        toolipText={formatMessage({ id: 'tasks.task-description-button-tooltip' })}
      />
      <TaskDescriptionEditor
        handleChange={(value: string) => {
          updateField('description')(value);

          return Promise.resolve(value);
        }}
        handleChangeChecklists={updateField('checklists')}
        value={task.description || ''}
        listVariables={listSystemVariables}
        templateVariables={templateVariables}
        accountId={accountId}
      />
    </div>
  );
}
