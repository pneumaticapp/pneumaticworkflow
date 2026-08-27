import { IFieldRuleSet } from '../../../../types/fieldset';
import { TRuleFieldOption } from '../RuleBase/types';

export interface IFieldRuleModalProps {
  isOpen: boolean;
  ruleset: IFieldRuleSet | null;
  rulesFieldOptions?: TRuleFieldOption[];
  onSave: (ruleset: IFieldRuleSet) => void;
  onClose: () => void;
}

export interface IFieldRulesetBodyProps {
  localRuleSet: IFieldRuleSet;
  rulesFieldOptions?: TRuleFieldOption[];
  onUpdateRuleSet: (changes: Partial<IFieldRuleSet>) => void;
}
