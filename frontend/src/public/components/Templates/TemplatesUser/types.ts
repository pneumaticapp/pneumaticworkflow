import { ITemplatesList } from '../../../types/redux';
import { ITemplateListItem } from '../../../types/template';
import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../../redux/actions';

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

export interface ITemplatesUserProps {
  templatesList: ITemplatesList;
  loading?: boolean;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  loadTemplates(offset: number): void;
  openRunWorkflowModal({ templateId }: { templateId: number }): void;
  setIsAITemplateModalOpened(value: boolean): void;
}
