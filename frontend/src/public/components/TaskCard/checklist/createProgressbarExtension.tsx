import * as React from 'react';

import { ChecklistProgressbarContainer, TChecklistProgressbarOwnProps } from './ChecklistProgressbar';

import { ITask } from '../../../types/tasks';

export function createProgressbarExtension(task: ITask) {
  const checklists: TChecklistProgressbarOwnProps[] = [];

  Object.values(task.checklists).forEach(checklist => {
    checklists.push({
      listApiName: checklist.apiName,
    })
  });

  return checklists.map(checklist => <ChecklistProgressbarContainer {...checklist} />);
}
