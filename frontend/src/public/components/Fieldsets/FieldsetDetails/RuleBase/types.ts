import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  EFieldsetNumberRulesetOperator,
  ERuleCombinator,
} from '../../../../types/fieldset';

export type TRuleHandlers = {
  updateRule: (params: {
    ruleGroupOrApiName: string;
    ruleGroupAndApiName: string;
    ruleChanges: Partial<IBaseRuleGroupAnd>;
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

export type TRuleItemProps = TRuleHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  ruleOperatorOptions: { apiName: EFieldsetNumberRulesetOperator; name: string }[];
  isReadOnly?: boolean;
};

export type TRuleListProps = TRuleHandlers & {
  ruleSet: IBaseRuleSet;
  isReadOnly?: boolean;
  addRule: () => void;
};

export type TRulesetMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};
