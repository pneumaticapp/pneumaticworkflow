export enum EModifyDropdownToggle {
  Modify = 'modify',
  More = 'more',
}

export interface IModifyDropdownProps {
  onEdit: () => void;
  onDelete: () => void;
  editLabel: string;
  deleteLabel: string;
  onClone?: () => void;
  cloneLabel?: string;
  className?: string;
  toggleType: EModifyDropdownToggle;
}
