import { IKickoffClient } from '../../../types/template';

export interface IKickoffLabelsProps {
  fields: IKickoffClient['fields'];
  onToggle(): void;
}
