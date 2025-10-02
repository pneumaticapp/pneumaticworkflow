import * as React from 'react';

import { TTaskCheckableItemOwnProps, TaskCheckableItemContainer } from './TaskCheckableItem';

import { ITask } from '../../../types/tasks';
import { EWorkflowStatus } from '../../../types/workflow';

export function createChecklistExtension(task: ITask) {
  const checks: TTaskCheckableItemOwnProps[] = [];

  Object.values(task.checklists).forEach(checklist => {
    Object.values(checklist.items).forEach(item => {
      checks.push({
        listApiName: checklist.apiName,
        itemApiName: item.apiName,
        disabled: task.isCompleted || task.workflow.status === EWorkflowStatus.Finished,
      })
    });
  });

  return checks.map(check => <TaskCheckableItemContainer {...check} />);
}
