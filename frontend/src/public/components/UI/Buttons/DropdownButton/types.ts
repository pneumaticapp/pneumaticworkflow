export interface IDropdownButtonOption {
  /** Stable identity for the list key. Falls back to the array index when omitted. */
  id?: string;
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
