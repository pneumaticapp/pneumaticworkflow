/* eslint-disable */
/* prettier-ignore */
import React, { useState } from 'react';

import { EMoveDirections } from '../../types/workflow';
import { ITemplateTask } from '../../types/template';
import { TUserListItem } from '../../types/user';

import { AddEntityButton, EEntityTitle, ITemplateEntity } from './AddEntityButton';
import { Delay } from './Delay';
import { WorkflowTaskFormContainer } from './TaskForm';
import { TaskItem } from './TaskItem';
import { TaskMenu } from './TaskMenu';
import { TTaskFormPart } from './types';

import styles from './TemplateEdit.css';

export interface ITemplateEntityProps {
  index: number;
  task: ITemplateTask;
  users: TUserListItem[];
  tasksCount: number;
  isSubscribed: boolean;
  isTaskOpen: boolean;
  isDelayOpen: boolean;
  addDelay(): void;
  addTaskBefore(): void;
  deleteDelay(targetTask: ITemplateTask): () => void;
  editDelay(delay: string): void;
  toggleDelay(): void;
  handleMoveTask(from: number, direction: EMoveDirections): () => void;
  removeTask(): void;
  toggleIsOpenTask(): void;
  cloneTask(): void;
}

export function TemplateEntity({
  task,
  index,
  users,
  tasksCount,
  isSubscribed,
  addDelay,
  addTaskBefore,
  deleteDelay,
  editDelay,
  isTaskOpen,
  isDelayOpen,
  toggleDelay,
  handleMoveTask,
  removeTask,
  toggleIsOpenTask,
  cloneTask,
}: ITemplateEntityProps) {
  const [scrollTarget, setScrollTarget] = useState<TTaskFormPart>(null);

  const renderAddWorkflowEntityButton = () => {
    const canAddDelay = task.number !== 1 && !task.delay;

    const entities = [
      {
        title: EEntityTitle.Task,
        onAddEntity: addTaskBefore,
      },
      canAddDelay && {
        title: EEntityTitle.Delay,
        onAddEntity: addDelay,
      },
    ].filter(Boolean) as ITemplateEntity[];

    return (
      <AddEntityButton
        key={`workflow-entity-${task.number}-add-button`}
        entities={entities}
      />
    );
  };

  const renderWorkflowEntity = () => {
    const entities = [
      {
        check: isTaskOpen,
        component: (
          <WorkflowTaskFormContainer
            task={task}
            users={users}
            scrollTarget={scrollTarget}
          />
        ),
      },
      {
        check: !isTaskOpen,
        component: (
          <TaskItem
            task={task}
            isSubscribed={isSubscribed}
            toggleIsOpenTask={toggleIsOpenTask}
            setScrollTarget={setScrollTarget}
          />
        ),
      },
    ];

    const { component } = entities.find(({ check }) => check) || {};

    if (!component) {
      return null;
    }

    return (
      <div key={`task-${task.uuid}`} className={styles['task-wrapper']}>
        {renderAddWorkflowEntityButton()}
        <div className={styles['task-wrapper__inner']}>
          {component}
          <TaskMenu
            task={task}
            isTaskOpen={isTaskOpen}
            tasksCount={tasksCount}
            removeTask={removeTask}
            cloneTask={cloneTask}
            moveTaskUp={handleMoveTask(index, EMoveDirections.Up)}
            moveTaskDown={handleMoveTask(index, EMoveDirections.Down)}
            addDelay={addDelay}
            toggleIsOpenTask={toggleIsOpenTask}
            setScrollTarget={setScrollTarget}
          />
        </div>
      </div>
    );
  };

  const renderDelay = () => {
    const hasDelay = Boolean(task?.delay);

    if (!hasDelay) {
      return null;
    }

    return (
      <div key={`delay-${task.uuid}`} className={styles['task-wrapper']}>
        {renderAddWorkflowEntityButton()}
        <Delay
          taskDelay={task.delay}
          isDelayOpen={isDelayOpen}
          deleteDelay={deleteDelay(task)}
          editDelay={editDelay}
          toggleDelay={toggleDelay}
        />
      </div>
    );
  };

  return (
    <>
      {renderDelay()}
      {renderWorkflowEntity()}
    </>
  );
}
