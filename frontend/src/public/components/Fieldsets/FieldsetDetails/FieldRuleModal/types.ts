import { IFieldRuleSet } from '../../../../types/fieldset';

export interface IFieldRuleModalProps {
  isOpen: boolean;
  ruleset: IFieldRuleSet | null;
  onSave: (ruleset: IFieldRuleSet) => void;
  onClose: () => void;
}

export interface IFieldRulesetBodyProps {
  localRuleSet: IFieldRuleSet;
  onUpdateRuleSet: (changes: Partial<IFieldRuleSet>) => void;
}
