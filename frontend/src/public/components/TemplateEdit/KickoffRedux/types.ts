import { IKickoff } from '../../../types/template';

export interface IKickoffLabelsProps {
  fields: IKickoff['fields'];
  onToggle(): void;
}
