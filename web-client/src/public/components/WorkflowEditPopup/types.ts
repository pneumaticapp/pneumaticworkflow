import { ITemplate } from '../../types/template';

export interface IRunWorkflow extends Pick<ITemplate, 'wfNameTemplate' | 'name' | 'kickoff' | 'description'> {
  id: number;
  tasksCount: number;
  performersCount: number;
  isUrgent?: boolean;
  ancestorTaskId?: number;
  dueDate?: string;
}
