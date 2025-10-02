/* eslint-disable */
import React from 'react';
import { useSelector } from 'react-redux';

import { getKickoff, getTemplateTasks } from '../../../redux/selectors/template';

import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { getVariables } from '../TaskForm/utils/getTaskVariables';

import { ITemplateTask } from '../../../types/template';
import { ETaskFormParts } from '../types';

import { TaskItemUsers } from './TaskItemUsers';
import { RichText } from '../../RichText';
import { TaskRenderDueIn } from '../TaskRenderDueInInfo';
import { TaskRenderReturnInfo } from '../TaskRenderReturnInfo';

import styles from '../TemplateEdit.css';
import { TaskRenderConditionsInfo } from '../TaskRenderConditionsInfo';

export interface ITaskItemProps {
  task: ITemplateTask;
  toggleIsOpenTask(): void;
  setScrollTarget(target: ETaskFormParts): void;
}

export const TaskItem = ({ task, toggleIsOpenTask, setScrollTarget }: ITaskItemProps) => {
  const { number, name, description, fields } = task;

  const kickoff = useSelector(getKickoff);
  const tasks = useSelector(getTemplateTasks);
  const allVariables = getVariables({ kickoff, tasks });

  const handleClickOnLabel = (taskFormParts: ETaskFormParts) => {
    setScrollTarget(taskFormParts);
    toggleIsOpenTask();
  };

  return (
    <div id={`task-form-${number}`} className={styles['task_view']} key={number}>
      <div className={styles['task__data-wrapper']}>
        <div className={styles['task_view-title']} onClick={toggleIsOpenTask}>
          <RichText text={name} variables={allVariables} isMarkdownMode={false} />
        </div>

        {description && (
          <div className={styles['task_view-description']} onClick={toggleIsOpenTask}>
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
