import { IExtraField } from '../../../../types/template';
import {
  IFieldsetRuleGroupAnd,
  IFieldsetRuleSet,
  EFieldsetNumberRulesetOperator,
} from '../../../../types/fieldset';

export type TRulePath = {
  rulesetApiName: string;
  ruleGroupOrApiName: string;
  ruleGroupAndApiName: string;
};

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

export type TFieldsetRulesListProps = {
  ruleSet: IFieldsetRuleSet;
  rulesets: IFieldsetRuleSet[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};

export type TFieldsetRuleItemProps = {
  groupAndRule: IFieldsetRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  rulesetApiName: string;
  rulesets: IFieldsetRuleSet[];
  ruleOperatorOptions: { apiName: EFieldsetNumberRulesetOperator; name: string }[];
  isReadOnly?: boolean;
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
};
