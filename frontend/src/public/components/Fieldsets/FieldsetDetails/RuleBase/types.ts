import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
  EFieldRuleType,
} from '../../../../types/fieldset';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';

export enum EFieldRuleShowOperator {
  Equal = 'equal',
  NotEqual = 'not_equals',
  Exist = 'exists',
  NotExist = 'not_exists',
  Contain = 'contains',
  NotContain = 'not_contains',
  GreaterThan = 'greater_than',
  LessThan = 'less_than',
}

export const FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE: EFieldRuleShowOperator[] = [
  EFieldRuleShowOperator.Exist,
  EFieldRuleShowOperator.NotExist,
];

export const SELECTION_FIELD_TYPES: EExtraFieldType[] = [
  EExtraFieldType.Checkbox,
  EExtraFieldType.Radio,
  EExtraFieldType.Creatable,
];


export type IFieldRuleBaseHandlers = {
  updateRule: (params: {
    groupOrApiName: string;
    groupAndApiName: string;
    ruleChanges: Partial<IBaseRuleGroupAnd>;
  }) => void;
  deleteRule: (params: {
    groupOrApiName: string;
    groupAndApiName: string;
  }) => void;
  regroupRules: (params: {
    groupOrApiName: string;
    groupAndApiName: string;
    ruleCombinator: ERuleCombinator;
  }) => void;
};

export type IFieldRuleBaseOperatorOption = {
  apiName: string;
  name: string;
};

export type IFieldRuleShowFieldOption = {
  apiName: string;
  name: string;
  type?: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
};

export type IFieldRuleBaseItemProps = IFieldRuleBaseHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  fieldRuleBaseOperatorOptions: IFieldRuleBaseOperatorOption[];
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
};

export type IFieldRuleBaseListProps = IFieldRuleBaseHandlers & {
  ruleSet: IBaseRuleSet;
  operatorOptions: { value: string; labelKey: string }[];
  fieldRuleShowFieldOptions?: IFieldRuleShowFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
  addRule: () => void;
};

export type IFieldRuleMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};

export type IFieldRuleShowItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRuleBaseOperatorOptions: IFieldRuleBaseOperatorOption[];
  fieldRuleShowFieldOptions: IFieldRuleShowFieldOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type IFieldRuleValidatorItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRuleBaseOperatorOptions: IFieldRuleBaseOperatorOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type IFieldRuleValueFieldProps = {
  fieldType?: EExtraFieldType;
  value: string;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  onChange: (value: string) => void;
};

