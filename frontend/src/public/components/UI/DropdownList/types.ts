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
  defaultValue?: TOption | TOption[] | null;
  onChange?(value: any, actionMeta: IDropdownActionMeta<TOption>): void;
  isMulti?: boolean;
  isSearchable?: boolean;
  isDisabled?: boolean;
  isRequired?: boolean;
  label?: string;
  title?: string;
  placeholder?: ReactNode;
  controlSize?: TControlSize;
  className?: string;
  controlClassName?: string;
  menuClassName?: string;
  placement?: TPlacement;
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

export interface IDropdownListSelectComponentsProps<TOption extends TDropdownOptionBase> extends Pick<
  IDropdownListProps<TOption>,
  | 'controlSize'
  | 'title'
  | 'label'
  | 'placeholder'
  | 'isMulti'
  | 'isSearchable'
  | 'isDisabled'
  | 'placement'
  | 'errorMessage'
  | 'controlClassName'
  | 'menuClassName'
  | 'noOptionsMessage'
  | 'getOptionLabel'
  | 'formatOptionLabel'
> {
  selectedLabel: ReactNode;
  selectValue: TOption[];
  searchText: string;
  staticMenu: boolean;
  isMenuOpen: boolean;
  onToggleMenu(): void;
  onCloseMenu(): void;
  onSearchChange(value: string): void;
}

export interface IDropdownOptionProps {
  label: ReactNode;
  isSelected?: boolean;
  withTooltip?: boolean;
  className?: string;
}
