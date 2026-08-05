import { RouteComponentProps } from 'react-router-dom';

import { IExtraField } from '../../../types/template';
import { EFieldLabelPosition, IFieldsetTemplateRule } from '../../../types/fieldset';

export interface IFieldsetDetailsRouteParams {
  id: string;
}

export type TFieldsetDetailsProps = RouteComponentProps<IFieldsetDetailsRouteParams>;

export type TDetailFieldsetState = {
  description: string;
  labelPosition: EFieldLabelPosition;
  fields: IExtraField[];
  rules: IFieldsetTemplateRule[];
};

export type TDetailFieldsetChanges = {
  description?: string;
  labelPosition?: EFieldLabelPosition;
  fields?: IExtraField[];
  rules?: IFieldsetTemplateRule[];
};

export type TFieldsetUnsavedChangesModalProps = {
  isChanged: boolean;
};
