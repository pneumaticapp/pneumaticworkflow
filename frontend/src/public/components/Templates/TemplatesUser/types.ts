import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../../redux/actions';
import { ITemplateListItem } from '../../../types/template';

export interface ITemplateCardProps extends ITemplateListItem {
  canEdit: boolean | undefined;
  onRunWorkflow(): void;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
}

export interface ITemplateCardFooterProps {
  templateId: number;
  tasksCount: number;
  isActive: boolean;
  onRunWorkflow(): void;
}
