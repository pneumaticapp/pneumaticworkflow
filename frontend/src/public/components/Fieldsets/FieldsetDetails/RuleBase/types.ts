import type { ReactNode } from 'react';
import type { TAvatarUser } from '../../../UI/Avatar/types';
import type {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
  EFieldRuleType,
  EFieldRuleValueType,
} from '../../../../types/fieldset';
import type { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';

export type IFieldRuleBaseHandlers = {
  updateRule: (params: {
    groupOrApiName: string;
    groupAndApiName: string;
    ruleChanges: Partial<IBaseRuleGroupAnd>;
  }) => void;
  deleteRule: (params: { groupOrApiName: string; groupAndApiName: string }) => void;
  regroupRules: (params: { groupOrApiName: string; groupAndApiName: string; ruleCombinator: ERuleCombinator }) => void;
};

export type TOperatorOption = {
  value: string;
  labelKey: string;
};

export type IFieldRuleBaseOperatorOption = {
  apiName: string;
  value: string;
  label: string;
};

export type IFieldRuleShowFieldOption = {
  apiName: string;
  name: string;
  type?: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
};

export type IRulesetRuleItemProps = IFieldRuleBaseHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  ruleType: EFieldRuleType;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
};

export type IRulesetRuleListProps = IFieldRuleBaseHandlers & {
  ruleSet: IBaseRuleSet;
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  ruleType: EFieldRuleType;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
  addRule: () => void;
};

export type IFieldRuleMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};

export type IRuleItemFieldOperatorValueProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRuleShowFieldOptions: IFieldRuleShowFieldOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type IRuleItemOperatorValueProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type TUserRuleDropdownOption = {
  apiName: string;
  name: ReactNode;
  searchByText: string;
  rawValue: string;
  valueType: EFieldRuleValueType;
};

export type TBuildUserDropdownOptionParams = {
  id: number;
  displayName: string;
  valueType: EFieldRuleValueType;
  avatarUser: TAvatarUser;
};

export type IRuleUserValueSelectProps = {
  value: string;
  valueType?: EFieldRuleValueType | null;
  isReadOnly?: boolean;
  onChange: (value: string, valueType: EFieldRuleValueType) => void;
};

export type IFieldRuleValueInputProps = {
  fieldType?: EExtraFieldType;
  value: string;
  valueType?: EFieldRuleValueType | null;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  onChange: (value: string, valueType?: EFieldRuleValueType | null) => void;
};

export type IRuleOperatorSelectProps = {
  fieldType?: EExtraFieldType;
  operator?: string | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
  onChange: (newOperator: string) => void;
};
