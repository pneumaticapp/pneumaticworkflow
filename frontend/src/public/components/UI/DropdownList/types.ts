import { ReactNode } from 'react';

export type TControlSize = 'lg' | 'sm';
export type TPlacement = 'left' | 'right';

export type TDropdownOptionBase = {
  label: string | ReactNode;
  sourceId?: string | null;
  value?: string;
  onClick?: () => void;
};

export type TDropdownOptionGroup<TOption> = {
  label: string;
  options: TOption[];
};

export type TDropdownListOptions<TOption> = Array<TOption | TDropdownOptionGroup<TOption>>;

/** Where the option label is rendered: inside the menu or inside the closed control. */
export type TOptionLabelContext = 'menu' | 'value';

export interface IFormatOptionLabelMeta<TOption> {
  context: TOptionLabelContext;
  selectValue: TOption[];
  inputValue: string;
}

export type TDropdownChangeAction = 'select-option' | 'deselect-option';

export interface IDropdownActionMeta<TOption> {
  action: TDropdownChangeAction;
  option?: TOption;
}

export interface IFilterCandidate<TOption> {
  label: string;
  value: string;
  data: TOption;
}

export interface IDropdownListProps<TOption extends TDropdownOptionBase> {
  options: TDropdownListOptions<TOption>;
  value?: TOption | TOption[] | null;
  /** Uncontrolled initial value. Ignored once `value` is passed. */
  defaultValue?: TOption | TOption[] | null;
  onChange?(value: any, actionMeta: IDropdownActionMeta<TOption>): void;
  isMulti?: boolean;
  isSearchable?: boolean;
  isDisabled?: boolean;
  isRequired?: boolean;
  /** Floating label above the `lg` control. */
  label?: string;
  /** Static caption for the `sm` control; falls back to the selected option label. */
  title?: string;
  placeholder?: ReactNode;
  controlSize?: TControlSize;
  className?: string;
  /** Applied to the closed control, so consumers can restyle it without reaching into internals. */
  controlClassName?: string;
  menuClassName?: string;
  /** Horizontal alignment of the `sm` menu against its control. */
  placement?: TPlacement;
  /** Renders the menu inline instead of in a popup, without a control. */
  staticMenu?: boolean;
  closeMenuOnSelect?: boolean;
  errorMessage?: string;
  noOptionsMessage?: string;
  getOptionLabel?(option: TOption): ReactNode;
  getOptionValue?(option: TOption): string;
  formatOptionLabel?(option: TOption, meta: IFormatOptionLabelMeta<TOption>): ReactNode;
  filterOption?(candidate: IFilterCandidate<TOption>, input: string): boolean;
  onInputChange?(value: string): void;
}

export interface IDropdownListMenuProps<TOption extends TDropdownOptionBase>
  extends Pick<
  IDropdownListProps<TOption>,
  'options' | 'isMulti' | 'isSearchable' | 'placeholder' | 'noOptionsMessage' | 'getOptionLabel' | 'formatOptionLabel'
  > {
  selectValue: TOption[];
  searchText: string;
  onSearchChange(value: string): void;
  onSelect(option: TOption): void;
  isSelected(option: TOption): boolean;
}

export interface IDropdownOptionProps {
  label: ReactNode;
  isSelected?: boolean;
  withTooltip?: boolean;
  className?: string;
}
