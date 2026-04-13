import { ITemplatesList } from '../../../types/redux';
import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../../redux/actions';

export interface ITemplatesUserProps {
  templatesList: ITemplatesList;
  loading?: boolean;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  loadTemplates(offset: number): void;
  openRunWorkflowModal({ templateId }: { templateId: number }): void;
  setIsAITemplateModalOpened(value: boolean): void;
}
