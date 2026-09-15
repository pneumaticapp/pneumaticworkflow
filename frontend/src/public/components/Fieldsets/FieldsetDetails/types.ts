import { RouteComponentProps } from 'react-router-dom';

import { IExtraField } from '../../../types/template';
import { EFieldLabelPosition, IFieldsetRuleSet } from '../../../types/fieldset';

export interface IFieldsetDetailsRouteParams {
  id: string;
}

export type TFieldsetDetailsProps = RouteComponentProps<IFieldsetDetailsRouteParams>;

export type TLocalFieldsetState = {
  title: string;
  description: string;
  labelPosition: EFieldLabelPosition;
  fields: IExtraField[];
  rulesets: IFieldsetRuleSet[];
};


export type TFieldsetChanges = {
  title?: string;
  description?: string;
  labelPosition?: EFieldLabelPosition;
  fields?: IExtraField[];
  rulesets?: IFieldsetRuleSet[];
};

export type TFieldsetUnsavedChangesModalProps = {
  isChanged: boolean;
  onSave: (onSuccess: () => void) => void;
};
