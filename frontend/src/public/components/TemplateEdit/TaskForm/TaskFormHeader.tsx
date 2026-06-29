import * as React from 'react';
import { useIntl } from 'react-intl';

import { ITemplateTask } from '../../../types/template';
import { TTaskVariable } from '../types';
import { InputWithVariables } from '../InputWithVariables';
import { TaskDescriptionEditor } from './TaskDescriptionEditor';
import { getSingleLineVariables } from './utils/getTaskVariables';

import styles from '../TemplateEdit.css';

interface ITaskFormHeaderProps {
  accountId: number;
  currentTask: ITemplateTask;
  listSystemVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  handleTaskFieldChange(field: keyof ITemplateTask): (value: ITemplateTask[keyof ITemplateTask]) => void;
}

export function TaskFormHeader({
  accountId,
  currentTask,
  handleTaskFieldChange,
  listSystemVariables,
  templateVariables,
}: ITaskFormHeaderProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['task-fields-wrapper']}>
      <InputWithVariables
        placeholder={formatMessage({ id: 'tasks.task-task-name-placeholder' })}
        listVariables={getSingleLineVariables(listSystemVariables)}
        templateVariables={templateVariables}
        value={currentTask.name || ''}
        onChange={(value: string) => {
          handleTaskFieldChange('name')(value);

          return Promise.resolve(value);
        }}
        className={styles['task-name-field']}
        toolipText={formatMessage({ id: 'tasks.task-description-button-tooltip' })}
      />
      <TaskDescriptionEditor
        handleChange={(value: string) => {
          handleTaskFieldChange('description')(value);

          return Promise.resolve(value);
        }}
        handleChangeChecklists={handleTaskFieldChange('checklists')}
        value={currentTask.description || ''}
        listVariables={listSystemVariables}
        templateVariables={templateVariables}
        accountId={accountId}
      />
    </div>
  );
}
