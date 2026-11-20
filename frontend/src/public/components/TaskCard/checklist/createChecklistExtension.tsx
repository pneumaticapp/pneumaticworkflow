import React from 'react';

import type { TTaskCheckableItemOwnProps } from './TaskCheckableItem/types';
import { TaskCheckableItemContainer } from './TaskCheckableItem';

import type { ITask } from '../../../types/tasks';
import { EWorkflowStatus } from '../../../types/workflow';

export function createChecklistExtension(task: ITask) {
  const checks: TTaskCheckableItemOwnProps[] = [];

  Object.values(task.checklists).forEach((checklist) => {
    Object.values(checklist.items).forEach((item) => {
      checks.push({
        listApiName: checklist.apiName,
        itemApiName: item.apiName,
        disabled: task.isCompleted || task.workflow.status === EWorkflowStatus.Finished,
      });
    });
  });

  return checks.map((check) => (
    <TaskCheckableItemContainer key={`${check.listApiName}_${check.itemApiName}`} {...check} />
  ));
}
