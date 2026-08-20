import { ITemplateClient, ITemplateKickoffClient, IRuntimeKickoffClient } from '../../types/template';
import { IFieldsetRuntime } from '../../types/fieldset';

export interface IRunWorkflow extends Omit<Pick<ITemplateClient, 'wfNameTemplate' | 'name' | 'kickoff' | 'description'>, 'kickoff'> {
  id: number;
  tasksCount: number;
  performersCount: number;
  kickoff: ITemplateKickoffClient | IRuntimeKickoffClient;
  isUrgent?: boolean;
  ancestorTaskId?: number;
  dueDate?: string;
  loadedFieldsets?: IFieldsetRuntime[];
}
