import { ITemplateClient, IFieldsetData } from '../../types/template';

export interface IRunWorkflow extends Pick<ITemplateClient, 'wfNameTemplate' | 'name' | 'kickoff' | 'description'> {
  id: number;
  tasksCount: number;
  performersCount: number;
  isUrgent?: boolean;
  ancestorTaskId?: number;
  dueDate?: string;
  loadedFieldsets?: IFieldsetData[];
}
