import { IExtraField } from '../../../../types/template';
import {
  IFieldsetRuleGroupAnd,
  IFieldsetRuleSet,
  EFieldsetNumberRulesetOperator,
  ERuleCombinator,
} from '../../../../types/fieldset';

export type TRuleHandlers = {
  updateRule: (params: {
    ruleGroupOrApiName: string;
    ruleGroupAndApiName: string;
    ruleChanges: Partial<IFieldsetRuleGroupAnd>;
  }) => void;
  deleteRule: (params: {
    ruleGroupOrApiName: string;
    ruleGroupAndApiName: string;
  }) => void;
  regroupRules: (params: {
    groupOrApiName: string;
    groupAndApiName: string;
    ruleCombinator: ERuleCombinator;
  }) => void;
};

export type TFieldsetRuleItemProps = TRuleHandlers & {
  groupAndRule: IFieldsetRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  ruleOperatorOptions: { apiName: EFieldsetNumberRulesetOperator; name: string }[];
  isReadOnly?: boolean;
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

export type TFieldsetRulesListProps = TRuleHandlers & {
  ruleSet: IFieldsetRuleSet;
  isReadOnly?: boolean;
  addRule: () => void;
};

export type TRulesetMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};

