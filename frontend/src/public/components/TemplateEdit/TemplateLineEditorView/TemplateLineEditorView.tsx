import * as React from 'react';
import { useCallback } from 'react';

import { ITemplateTaskClient } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { EMoveDirections } from '../../../types/workflow';
import { ITemplateEditorController } from '../types';
import { KickoffReduxContainer } from '../KickoffRedux';
import { TemplateEntity } from '../TemplateEntity';
import { AddEntityButton, EEntityTitle } from '../AddEntityButton';
import { TemplateIntegrations } from '../Integrations';

import styles from '../TemplateEdit.css';

export interface ITemplateLineEditorViewProps {
  users: TUserListItem[];
  isSubscribed: boolean;
  controller: ITemplateEditorController;
}

export function TemplateLineEditorView({ users, isSubscribed, controller }: ITemplateLineEditorViewProps) {
  const {
    sortedTasks,
    openedTasks,
    openedDelays,
    setKickoff,
    addTask,
    addTaskBefore,
    removeTask,
    cloneTask,
    moveTask,
    addDelay,
    editDelay,
    deleteDelay,
    toggleTask,
    toggleDelay,
  } = controller;

  const renderTask = useCallback(
    (task: ITemplateTaskClient, index: number, tasks: ITemplateTaskClient[]) => {
      const previousTask = index > 0 ? tasks[index - 1] : null;

      return (
        <TemplateEntity
          key={`template-entity-${task.uuid}`}
          index={index}
          task={task}
          users={users}
          tasksCount={tasks.length}
          isSubscribed={isSubscribed}
          removeTask={() => removeTask(task)}
          cloneTask={() => cloneTask(task)}
          addDelay={() => addDelay(task)}
          addTaskBefore={(previousTaskApiName?: string) => addTaskBefore(task, previousTaskApiName)}
          deleteDelay={(targetTask) => () => deleteDelay(targetTask)}
          editDelay={(delay) => editDelay(task, delay)}
          isTaskOpen={Boolean(openedTasks[task.uuid])}
          isDelayOpen={Boolean(openedDelays[task.uuid])}
          toggleDelay={() => toggleDelay(task.uuid)}
          handleMoveTask={(from: number, direction: EMoveDirections) => () => moveTask(from, direction)}
          toggleIsOpenTask={() => toggleTask(task.uuid)}
          actualPreviousTaskApiName={previousTask?.apiName}
        />
      );
    },
    [
      addDelay,
      addTaskBefore,
      cloneTask,
      deleteDelay,
      editDelay,
      isSubscribed,
      moveTask,
      openedDelays,
      openedTasks,
      removeTask,
      toggleDelay,
      toggleTask,
      users,
    ],
  );

  return (
    <div className={styles['tasks']} data-test-id="template-line-editor">
      <div className={styles['kickoff-wrapper']}>
        <KickoffReduxContainer setKickoff={setKickoff} />
      </div>
      {sortedTasks.map(renderTask)}
      <AddEntityButton
        entities={[
          {
            title: EEntityTitle.Task,
            onAddEntity: addTask,
          },
        ]}
      />
      <TemplateIntegrations />
    </div>
  );
}
