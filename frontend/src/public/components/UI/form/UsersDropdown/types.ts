import { ReactNode } from 'react';
import { FormatOptionLabelMeta } from 'react-select';

import { IDropdownListProps, TDropdownOptionBase } from '../../DropdownList';
import { ETaskPerformerType } from '../../../../types/template';
import { TUserListItem } from '../../../../types/user';

export enum EOptionTypes {
  Group = ETaskPerformerType.UserGroup,
  User = ETaskPerformerType.User,
  Starter = ETaskPerformerType.WorkflowStarter,
  Field = ETaskPerformerType.OutputUser,
  Manager = ETaskPerformerType.Manager,
  InviteUsers = 'invite-users',
  AllUsers = 'all-users',
}

export type TUsersDropdownOption = TDropdownOptionBase & {
  firstName?: string;
  lastName?: string;
  id: number;
  optionType: EOptionTypes;
};

export interface IUsersDropdownProps<TOption extends TUsersDropdownOption> extends IDropdownListProps<TOption> {
  inviteLabel: string;
  users: TUserListItem[];
  isTeamInvitesModalOpen: boolean;
  recentInvitedUsers: TUserListItem[];
  isAdmin: boolean;
  value?: any;
  onChange: (value: any) => void;
  onChangeSelected?: (value: any) => void;
  openTeamInvitesPopup(): void;
  onUsersInvited?(invitedUsers: any): void;
  onClickInvite(): void;
  onClickAllUsers?(value: boolean): void;
  errorMessage?: string;
  isRequired?: boolean;
}

export interface IUsersDropdownOptionProps {
  option: TUsersDropdownOption;
  formatOptionLabelMeta: FormatOptionLabelMeta<TUsersDropdownOption>;
  users: TUserListItem[];
  isMulti?: boolean;
  isSelectAll: boolean;
  isIndeterminate: boolean;
  hasValue: boolean;
  showAllUsers: boolean;
  customLabel?: ReactNode;
}
