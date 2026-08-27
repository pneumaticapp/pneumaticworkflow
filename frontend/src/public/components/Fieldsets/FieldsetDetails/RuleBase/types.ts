import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
  EFieldRuleType,
} from '../../../../types/fieldset';

import { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';

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
export type TRuleFieldOption = {
  apiName: string;
  name: string;
  type?: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
};

export type TRuleItemProps = TRuleHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  ruleOperatorOptions: TRuleOperatorOption[];
  rulesFieldOptions?: TRuleFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
};

export type TRuleListProps = TRuleHandlers & {
  ruleSet: IBaseRuleSet;
  operatorOptions: { value: string; labelKey: string }[];
  rulesFieldOptions?: TRuleFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
  addRule: () => void;
};

export type TRulesetMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};

export type TRuleItemShowProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  ruleOperatorOptions: TRuleOperatorOption[];
  rulesFieldOptions: TRuleFieldOption[];
  isReadOnly?: boolean;
  updateRule: TRuleHandlers['updateRule'];
};

export type TRuleItemValidatorProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  ruleOperatorOptions: TRuleOperatorOption[];
  isReadOnly?: boolean;
  updateRule: TRuleHandlers['updateRule'];
};

export type TFieldsetFieldRulesValueProps = {
  fieldType?: EExtraFieldType;
  value: string;
  selections?: IExtraFieldSelection[] | string[];
  isReadOnly?: boolean;
  onChange: (value: string) => void;
};
