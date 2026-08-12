import { ChangeEvent, ReactNode, SVGAttributes } from 'react';

export type TOptionId = number | string | null;
export type TOptionBase<IdKey extends string, LabelKey extends string> = {
  [key in IdKey]: TOptionId;
} & {
  [key in LabelKey]: string | ReactNode;
} & {
  customClickHandler?(): void;
  areSubOptionsLoading?: boolean;
  count?: number;
  subTitle?: string;
  searchByText?: string;
  isTitle?: boolean;
  type?: string;
};

interface IFilterSelectCommonProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  isLoading?: boolean;
  options: TOption[];
  groupedOptions?: Map<number, { title: string; options: TOption[] }>;
  flatGroupedOptions?: TOption[];
  isSearchShown?: boolean;
  isDisabled?: boolean;
  noValueLabel?: string;
  placeholderText: string;
  searchPlaceholder?: string;
  toggleClassName?: string;
  arrowClassName?: string;
  menuClassName?: string;
  isWideMenu?: boolean;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  containerClassname?: string;
  selectAllLabel?: string;
  resetFilter(): void;
  selectAll?(): void;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  renderPlaceholder(options: TOption[]): string | JSX.Element;
  positionFixed?: boolean;
  getOptionSelectionKey?: (option: TOption) => TOptionId;
}

interface IFilterSelectMultiOptionsProps {
  isMultiple: true;
  selectedOption?: never;
  selectedOptions: TOptionId[];
  onChange(optionIds: TOptionId[] | string[], option: unknown): void;
}

interface IFilterSelectSingleOptionsProps {
  isMultiple?: false;
  selectedOption: TOptionId;
  selectedOptions?: never;
  onChange(optionId: TOptionId | string | null): void;
}

export type TFilterSelectProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> = IFilterSelectCommonProps<IdKey, LabelKey, TOption> &
  (IFilterSelectMultiOptionsProps | IFilterSelectSingleOptionsProps);

export interface IFilterSelectMenuProps<
  IdKey extends string,
  LabelKey extends string,
  TOption extends TOptionBase<IdKey, LabelKey>,
> {
  options: Array<TOption | string>;
  optionIdKey: IdKey;
  optionLabelKey: LabelKey;
  selectedOptionId: number | string | null | undefined;
  isMultiple: boolean;
  isLoading?: boolean;
  isSearchShown?: boolean;
  searchText: string;
  searchPlaceholder?: string;
  placeholderText: string;
  noValueLabel?: string;
  selectAllLabel?: string;
  isSelectAll: boolean;
  isSelected(option: TOption): boolean;
  onSearchChange(event: ChangeEvent<HTMLInputElement>): void;
  onClearSearch(): void;
  onReset(): void;
  onSelectAll(): void;
  onSelect(option: TOption): void;
  closeDropdown(): void;
}

export interface ISelectMenuProps<T extends string> {
  withRadio?: boolean;
  activeValue: T;
  values: T[];
  toggleClassName?: string;
  toggleTextClassName?: string;
  arrowClassName?: string;
  menuClassName?: string;
  containerClassName?: string;
  isDisabled?: boolean;
  hideSelectedOption?: boolean;
  closeOnSelect?: boolean;
  onChange(value: T): void;
  Icon?(props: SVGAttributes<SVGElement>): JSX.Element;
  isFromCheckIfConditions?: boolean;
  positionFixed?: boolean;
  activeValueLabelId?: string;
}
