import { IExtraField } from '../../../../types/template';
import { IFieldsetRuleSet } from '../../../../types/fieldset';

export {
  TRuleHandlers,
  TRuleItemProps as TFieldsetRuleItemProps,
  TRuleListProps as TFieldsetRulesListProps,
  TRulesetMessageInputProps,
} from '../RuleBase/types';

export type TRulesetsParams = {
  rulesets: IFieldsetRuleSet[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
};

export type TRulesetParams = TRulesetsParams & {
  rulesetApiName: string;
};

export type TFieldsetRulesetsProps = {
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};
