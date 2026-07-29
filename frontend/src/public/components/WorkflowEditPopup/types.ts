import { ITemplateClient } from '../../types/template';
import { IFieldsetRuntime } from '../../types/fieldset';

export interface IRunWorkflow extends Pick<ITemplateClient, 'wfNameTemplate' | 'name' | 'kickoff' | 'description'> {
  id: number;
  tasksCount: number;
  performersCount: number;
  isUrgent?: boolean;
  ancestorTaskId?: number;
  dueDate?: string;
  loadedFieldsets?: IFieldsetRuntime[];
}
