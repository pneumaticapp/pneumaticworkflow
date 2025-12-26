export type TOptionId = number | string | null;
export type TSubOption<IdKey extends string, LabelKey extends string> = TOptionBase<IdKey, LabelKey> & {
  count?: number;
};

export type TOptionBase<IdKey extends string, LabelKey extends string> = {
  [key in IdKey]: TOptionId;
} & {
  [key in LabelKey]: string | React.ReactNode;
} & {
  customClickHandler?(): void;
  areSubOptionsLoading?: boolean;
  subOptions?: TSubOption<IdKey, LabelKey>[];
  count?: number;
};

export interface IFilterCommonProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  title: string;
  optionsTitle?: string;
  isInitiallyExpanded?: boolean;
  options: TOption[];
  isLoading?: boolean;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  optionApiNameKey?: string;
  containerClassName?: string;
  withSearch?: boolean;
  selectedSubOptions?: TOptionId[];
  renderOptionTitle?(option: TOption): React.ReactNode;
  onCheckOption?(option: TOption, callback?: () => void): void;
  onUncheckOption?(option: TOption, callback?: () => void): void;
  onCheckSubOption?(optionId: TOptionId, subOptionId: TOptionId): void;
  onUncheckSubOption?(optionId: TOptionId, subOptionId: TOptionId): void;
  onExpandOption?(option: TOption): void;
}

export interface IFilterMultiOptionsProps {
  isMultiple: true;
  selectedOption?: never;
  selectedOptions: TOptionId[];
  changeFilter(optionIds: TOptionId[], option: any): void;
}

export interface IFilterSingleOptionsProps {
  isMultiple?: false;
  selectedOption: TOptionId;
  selectedOptions?: never;
  changeFilter(optionId: TOptionId | null): void;
}

export type TFilterProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> = IFilterCommonProps<IdKey, LabelKey, TOption> & (IFilterMultiOptionsProps | IFilterSingleOptionsProps);
