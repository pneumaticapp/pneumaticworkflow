import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
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

export type TRuleOperatorOption = { apiName: string; name: string };

export type TRuleItemProps = TRuleHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  ruleOperatorOptions: TRuleOperatorOption[];
  isReadOnly?: boolean;
};

export type TRuleListProps = TRuleHandlers & {
  ruleSet: IBaseRuleSet;
  operatorOptions: { value: string; labelKey: string }[];
  isReadOnly?: boolean;
  addRule: () => void;
};

export type TRulesetMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};
