import React from 'react';
import { useSelector } from 'react-redux';

import { getKickoff, getTemplateData, getTemplateTasks } from '../../../redux/selectors/template';

import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { getVariables } from '../TaskForm/utils/getTaskVariables';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview/FieldsetOutputsPreview';

import { ITemplateTaskClient } from '../../../types/template';
import { ETaskFormParts } from '../types';

import { TaskItemUsers } from './TaskItemUsers';
import { RichText } from '../../RichText';
import { TaskRenderDueIn } from '../TaskRenderDueInInfo';
import { TaskRenderReturnInfo } from '../TaskRenderReturnInfo';

import { TemplateValidationError } from '../TemplateValidationError';
import styles from '../TemplateEdit.css';
import { TaskRenderConditionsInfo } from '../TaskRenderConditionsInfo';

export interface ITaskItemProps {
  task: ITemplateTaskClient;
  toggleIsOpenTask(): void;
  setScrollTarget(target: ETaskFormParts): void;
}

export const TaskItem = ({ task, toggleIsOpenTask, setScrollTarget }: ITaskItemProps) => {
  const { number, name, description, fields } = task;

  const kickoff = useSelector(getKickoff);
  const tasks = useSelector(getTemplateTasks);
  const template = useSelector(getTemplateData);
  const allVariables = getVariables({
    kickoff,
    tasks,
    templateId: template.id,
  });

  const handleClickOnLabel = (taskFormParts: ETaskFormParts) => {
    setScrollTarget(taskFormParts);
    toggleIsOpenTask();
  };

  const handleToggleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;

    event.preventDefault();
    toggleIsOpenTask();
  };

  return (
    <div id={`task-form-${number}`} className={styles['task_view']} key={number}>
      <div className={styles['task__data-wrapper']}>
        <div
          className={styles['task_view-title']}
          role="button"
          tabIndex={0}
          onClick={toggleIsOpenTask}
          onKeyDown={handleToggleKeyDown}
        >
          <RichText text={name} variables={allVariables} isMarkdownMode={false} />
        </div>
        <TemplateValidationError apiNames={[task.apiName]} section={null} />

        {description && (
          <div
            className={styles['task_view-description']}
            role="button"
            tabIndex={0}
            onClick={toggleIsOpenTask}
            onKeyDown={handleToggleKeyDown}
          >
            <RichText text={description} variables={allVariables} />
          </div>
        )}

        <div className={styles['task-preview-performers']}>
          <div className={styles['task-preview-performers__inner']}>
            <TaskItemUsers task={task} onClick={() => handleClickOnLabel(ETaskFormParts.AssignPerformers)} />
            {TaskRenderDueIn({ task, onClick: () => handleClickOnLabel(ETaskFormParts.DueIn) })}
          </div>
        </div>

        <div className={styles['task-preview-outputs']}>
          <ExtraFieldsLabels extraFields={fields} onClick={() => handleClickOnLabel(ETaskFormParts.Fields)} />
          <FieldsetOutputsPreview
            fieldsets={task.fieldsets || []}
            onGroupClick={() => handleClickOnLabel(ETaskFormParts.Fields)}
          />
          {TaskRenderConditionsInfo({
            task,
            onClick: () => handleClickOnLabel(ETaskFormParts.StartsAfter),
            isStartTask: true,
          })}
          {TaskRenderConditionsInfo({ task, onClick: () => handleClickOnLabel(ETaskFormParts.CheckIf) })}
          {TaskRenderReturnInfo({ task, onClick: () => handleClickOnLabel(ETaskFormParts.ReturnTo) })}
        </div>
      </div>
    </div>
  );
};
