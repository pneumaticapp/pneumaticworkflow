import { ITaskListItem } from '../../types/tasks';

export type TLoadFilterStepsPayload = { templateId: number };

export type TPatchTaskInListPayload = {
  taskId: number;
  task: Partial<ITaskListItem>;
};

export type TShiftTaskListPayload = { currentTaskId: number };
