import { ITemplateKickoffClient } from '../../../types/template';

export interface IKickoffLabelsProps {
  fields: ITemplateKickoffClient['fields'];
  onToggle(): void;
}
