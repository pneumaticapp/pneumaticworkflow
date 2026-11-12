import React from 'react';

import type { TChecklistProgressbarOwnProps } from './ChecklistProgressbar';
import { ChecklistProgressbarContainer } from './ChecklistProgressbar';

import type { ITask } from '../../../types/tasks';

export function createProgressbarExtension(task: ITask) {
  const checklists: TChecklistProgressbarOwnProps[] = [];

  Object.values(task.checklists).forEach((checklist) => {
    checklists.push({
      listApiName: checklist.apiName,
    });
  });

  return checklists.map((checklist) => <ChecklistProgressbarContainer key={checklist.listApiName} {...checklist} />);
}
