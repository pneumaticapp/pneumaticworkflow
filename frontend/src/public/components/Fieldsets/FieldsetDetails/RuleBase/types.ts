import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
  EFieldRuleType,
  EFieldRuleOperator,
} from '../../../../types/fieldset';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';

export { EFieldRuleOperator };

export const FIELD_RULE_OPERATORS_WITHOUT_VALUE: EFieldRuleOperator[] = [
  EFieldRuleOperator.Exist,
  EFieldRuleOperator.NotExist,
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

export type TOperatorOption = {
  value: string;
  labelKey: string;
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

export type IFieldRuleShowItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRuleShowFieldOptions: IFieldRuleShowFieldOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type IFieldRuleValidatorItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldType: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
  updateRule: IFieldRuleBaseHandlers['updateRule'];
};

export type IFieldRuleValueInputProps = {
  fieldType?: EExtraFieldType;
  value: string;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  onChange: (value: string) => void;
};

export type IRuleOperatorSelectProps = {
  fieldType?: EExtraFieldType;
  operator?: string | null;
  isReadOnly?: boolean;
  isFieldsetRuleset?: boolean;
  onChange: (newOperator: string) => void;
};

