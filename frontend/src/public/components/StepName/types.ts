import type { TLoadTemplateVariablesPayload } from '../../redux/templates/actions';
import type { TTaskVariable } from '../../types/template';

export interface IStepNameProps {
  initialStepName: string;
  templateId: number;
  variables?: TTaskVariable[];
  loadTemplateVariables(payload: TLoadTemplateVariablesPayload): void;
}
