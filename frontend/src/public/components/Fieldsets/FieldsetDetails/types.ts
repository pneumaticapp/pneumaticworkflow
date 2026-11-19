import type { RouteComponentProps } from 'react-router-dom';

import type { IExtraField } from '../../../types/template';
import type { EFieldLabelPosition, IFieldsetTemplateRule } from '../../../types/fieldset';

export interface IFieldsetDetailsRouteParams {
  id: string;
}

export type TFieldsetDetailsProps = RouteComponentProps<IFieldsetDetailsRouteParams>;

export type TDetailFieldsetState = {
  title: string;
  description: string;
  labelPosition: EFieldLabelPosition;
  fields: IExtraField[];
  rules: IFieldsetTemplateRule[];
};

export type TDetailFieldsetChanges = {
  title?: string;
  description?: string;
  labelPosition?: EFieldLabelPosition;
  fields?: IExtraField[];
  rules?: IFieldsetTemplateRule[];
};

export type TFieldsetUnsavedChangesModalProps = {
  isChanged: boolean;
  onSave: (onSuccess: () => void) => void;
};
