import React, { useState } from 'react';
import { EMoveDirections } from '../../../types/workflow';
import { AddEntityButton, EEntityTitle, ITemplateEntity } from '../AddEntityButton';
import { Delay } from '../Delay';
import { WorkflowTaskFormContainer } from '../TaskForm';
import { TaskItem } from '../TaskItem';
import { TaskMenu } from '../TaskMenu';
import { TTaskFormPart } from '../types';
import { ITemplateEntityProps } from './TemplateEntity.props';
import styles from './TemplateEntity.css';

export function TemplateEntity({
  task,
  index,
  users,
  tasksCount,
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

    return <AddEntityButton key={`workflow-entity-${task.number}-add-button`} entities={entities} />;
  };

  const renderWorkflowEntity = () => {
    const entities = [
      {
        check: isTaskOpen,
        component: <WorkflowTaskFormContainer task={task} users={users} scrollTarget={scrollTarget} />,
      },
      {
        check: !isTaskOpen,
        component: <TaskItem task={task} toggleIsOpenTask={toggleIsOpenTask} setScrollTarget={setScrollTarget} />,
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
