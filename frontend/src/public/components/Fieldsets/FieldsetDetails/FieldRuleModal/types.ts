import { IFieldRuleSet } from '../../../../types/fieldset';
import { IFieldRuleShowFieldOption } from '../RuleBase/types';

export interface IFieldRuleModalProps {
  isOpen: boolean;
  ruleset: IFieldRuleSet | null;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  onSave: (ruleset: IFieldRuleSet) => void;
  onClose: () => void;
}

export interface IFieldRulesetBodyProps {
  localRuleSet: IFieldRuleSet;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  onUpdateRuleSet: (changes: Partial<IFieldRuleSet>) => void;
}
