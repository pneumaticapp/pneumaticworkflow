import { IExtraField } from '../../../../types/template';
import { IFieldRuleSet } from '../../../../types/fieldset';

export interface IDatasetOption {
  label: string;
  value: string;
}

export interface IKickoffDropdownProps {
  apiName?: string;
  isRequired: boolean;
  isRequiredDisabled: boolean;
  isHidden?: boolean;
  isFirstItem?: boolean;
  isLastItem?: boolean;
  onEditField(changedProps: Partial<IExtraField>): void;
  onDeleteField(): void;
  onMoveFieldUp(): void;
  onMoveFieldDown(): void;
  showDatasetOption: boolean;
  datasetOptions: IDatasetOption[];
  selectedDatasetId?: number;
  onDatasetSelect: (datasetId: number) => void;
  fieldType?: string;
  fieldRulesets?: IFieldRuleSet[];
  onOpenFieldRules?(ruleset?: IFieldRuleSet): void;
  onDeleteFieldRuleset?(rulesetApiName: string): void;
}

export interface IDeletableDropdownOptionProps {
  label: string;
  onDelete(): void;
  onClick?(): void;
}
