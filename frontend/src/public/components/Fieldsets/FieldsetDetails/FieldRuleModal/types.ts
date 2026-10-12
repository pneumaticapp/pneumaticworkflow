import { IFieldRuleSet } from '../../../../types/fieldset';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';
import { IFieldRuleShowFieldOption } from '../RuleBase/types';

export interface IFieldRuleModalProps {
  isOpen: boolean;
  ruleset: IFieldRuleSet | null;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  onSave: (ruleset: IFieldRuleSet) => void;
  onClose: () => void;
}

export interface IFieldRulesetBodyProps {
  localRuleSet: IFieldRuleSet;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  onUpdateRuleSet: (changes: Partial<IFieldRuleSet>) => void;
}
