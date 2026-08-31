import { IFieldRuleSet } from '../../../../types/fieldset';
import { IFieldRulesetShowFieldOption } from '../RuleBase/types';

export interface IFieldRuleModalProps {
  isOpen: boolean;
  ruleset: IFieldRuleSet | null;
  fieldRulesetShowFieldOptions?: IFieldRulesetShowFieldOption[];
  onSave: (ruleset: IFieldRuleSet) => void;
  onClose: () => void;
}

export interface IFieldRulesetBodyProps {
  localRuleSet: IFieldRuleSet;
  fieldRulesetShowFieldOptions?: IFieldRulesetShowFieldOption[];
  onUpdateRuleSet: (changes: Partial<IFieldRuleSet>) => void;
}
