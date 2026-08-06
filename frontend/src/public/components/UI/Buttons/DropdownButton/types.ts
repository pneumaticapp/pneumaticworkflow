export interface IDropdownButtonOption {
  itemHeaderIntlId?: string;
  itemDescriptionIntlId?: string;
  onClick(): void;
}

export interface IDropdownButtonProps {
  dropdownOptions: IDropdownButtonOption[];
  isLoading?: boolean;
  isDisabled?: boolean;
  className?: string;
}
