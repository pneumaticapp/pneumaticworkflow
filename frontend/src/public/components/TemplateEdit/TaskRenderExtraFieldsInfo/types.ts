import { ITemplateTaskClient } from '../../../types/template';

export interface ITaskRenderExtraFieldsInfoProps {
  task: ITemplateTaskClient;
  onClick(): void;
}
