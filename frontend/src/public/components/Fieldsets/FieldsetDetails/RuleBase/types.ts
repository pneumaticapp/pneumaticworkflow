import {
  IBaseRuleGroupAnd,
  IBaseRuleSet,
  ERuleCombinator,
  EFieldRuleType,
} from '../../../../types/fieldset';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../types/template';

export type IFieldRulesetBaseHandlers = {
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

export type IFieldRulesetBaseOperatorOption = {
  apiName: string;
  name: string;
};

export type IFieldRulesetShowFieldOption = {
  apiName: string;
  name: string;
  type?: EExtraFieldType;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
};

export type IFieldRulesetBaseItemProps = IFieldRulesetBaseHandlers & {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  groupOrIndex: number;
  groupAndIndex: number;
  fieldRulesetBaseOperatorOptions: IFieldRulesetBaseOperatorOption[];
  fieldRulesetShowFieldOptions?: IFieldRulesetShowFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
};

export type IFieldRulesetBaseListProps = IFieldRulesetBaseHandlers & {
  ruleSet: IBaseRuleSet;
  operatorOptions: { value: string; labelKey: string }[];
  fieldRulesetShowFieldOptions?: IFieldRulesetShowFieldOption[];
  ruleType: EFieldRuleType;
  isReadOnly?: boolean;
  addRule: () => void;
};

export type IFieldRulesetMessageInputProps = {
  message?: string | null;
  onChange: (message: string) => void;
  isReadOnly?: boolean;
};

export type IFieldRulesetShowItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRulesetBaseOperatorOptions: IFieldRulesetBaseOperatorOption[];
  fieldRulesetShowFieldOptions: IFieldRulesetShowFieldOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRulesetBaseHandlers['updateRule'];
};

export type IFieldRulesetValidatorItemProps = {
  groupAndRule: IBaseRuleGroupAnd;
  groupOrApiName: string;
  fieldRulesetBaseOperatorOptions: IFieldRulesetBaseOperatorOption[];
  isReadOnly?: boolean;
  updateRule: IFieldRulesetBaseHandlers['updateRule'];
};

export type IFieldRulesetValueFieldProps = {
  fieldType?: EExtraFieldType;
  value: string;
  selections?: IExtraFieldSelection[] | string[];
  datasetId?: number | null;
  isReadOnly?: boolean;
  onChange: (value: string) => void;
};

