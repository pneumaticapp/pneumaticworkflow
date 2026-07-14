import React, { useMemo, useState } from 'react';

import { ChecklistProgressbar } from '../../TaskCard/checklist/ChecklistProgressbar/ChecklistProgressbar';
import { TaskCheckableItem } from '../../TaskCard/checklist/TaskCheckableItem/TaskCheckableItem';
import type { ITask, TTaskChecklistsItem } from '../../../types/tasks';
import { EWorkflowStatus } from '../../../types/workflow';
import { RichText } from '../RichText';
import type { IRichTextProps } from '../types';

interface ICreateStoryTaskOptions {
  listApiName: string;
  itemApiNames: string[];
  checkedItemApiNames?: string[];
}

export const createStoryTask = ({
  listApiName,
  itemApiNames,
  checkedItemApiNames = [],
}: ICreateStoryTaskOptions): ITask => {
  const checkedSet = new Set(checkedItemApiNames);
  const items = Object.fromEntries(
    itemApiNames.map((apiName, index) => [
      apiName,
      {
        id: index + 1,
        apiName,
        isSelected: checkedSet.has(apiName),
      } satisfies TTaskChecklistsItem,
    ]),
  );
  const checkedItems = itemApiNames.filter((apiName) => checkedSet.has(apiName)).length;

  return {
    id: 1,
    name: 'Story task',
    description: null,
    output: [],
    workflow: {
      id: 1,
      name: 'Workflow',
      status: EWorkflowStatus.Running,
      templateName: 'Template',
      dateCompleted: null,
    },
    performers: [],
    containsComments: false,
    isCompleted: false,
    dateStarted: '2024-01-01T00:00:00Z',
    dateCompleted: null,
    dueDate: null,
    isUrgent: false,
    subWorkflows: [],
    areChecklistsHandling: false,
    checklistsTotal: itemApiNames.length,
    checklistsMarked: checkedItems,
    revertTasks: [],
    checklists: {
      [listApiName]: {
        id: 1,
        apiName: listApiName,
        checkedItems,
        totalItems: itemApiNames.length,
        items,
      },
    },
  };
};

const toggleStoryChecklistItem = (
  task: ITask,
  listApiName: string,
  itemApiName: string,
  isChecked: boolean,
): ITask => {
  const checklist = task.checklists[listApiName];
  const item = checklist?.items[itemApiName];

  if (!checklist || !item || item.isSelected === isChecked) {
    return task;
  }

  const checkedDelta = isChecked ? 1 : -1;

  return {
    ...task,
    checklistsMarked: task.checklistsMarked + checkedDelta,
    checklists: {
      ...task.checklists,
      [listApiName]: {
        ...checklist,
        checkedItems: checklist.checkedItems + checkedDelta,
        items: {
          ...checklist.items,
          [itemApiName]: {
            ...item,
            isSelected: isChecked,
          },
        },
      },
    },
  };
};

const createStoryChecklistExtensions = (
  task: ITask,
  onToggleItem: (listApiName: string, itemApiName: string, isChecked: boolean) => void,
): React.ReactNode[] => {
  const extensions: React.ReactNode[] = [];

  Object.values(task.checklists).forEach((checklist) => {
    extensions.push(
      <ChecklistProgressbar
        key={`progressbar-${checklist.apiName}`}
        listApiName={checklist.apiName}
        checkedItems={checklist.checkedItems}
        totalItems={checklist.totalItems}
      />,
    );

    Object.values(checklist.items).forEach((item) => {
      extensions.push(
        <TaskCheckableItem
          key={`checklist-${checklist.apiName}-${item.apiName}`}
          listApiName={checklist.apiName}
          itemApiName={item.apiName}
          isChecked={item.isSelected}
          markChecklistItem={() => onToggleItem(checklist.apiName, item.apiName, true)}
          unmarkChecklistItem={() => onToggleItem(checklist.apiName, item.apiName, false)}
        />,
      );
    });
  });

  return extensions;
};

interface IInteractiveRichTextProps extends Omit<IRichTextProps, 'interactiveChecklists' | 'renderExtensions'> {
  task: ITask;
}

export const InteractiveRichText = ({ task: initialTask, ...props }: IInteractiveRichTextProps) => {
  const [task, setTask] = useState(initialTask);

  const handleToggleItem = (listApiName: string, itemApiName: string, isChecked: boolean) => {
    setTask((currentTask) => toggleStoryChecklistItem(currentTask, listApiName, itemApiName, isChecked));
  };

  const renderExtensions = useMemo(
    () => createStoryChecklistExtensions(task, handleToggleItem),
    [task],
  );

  return (
    <RichText
      {...props}
      interactiveChecklists
      renderExtensions={renderExtensions}
    />
  );
};
