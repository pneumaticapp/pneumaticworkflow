import type { IDropdownListProps, TDropdownOptionBase } from '../../DropdownList/types';
import type { IGroup } from '../../../../types/team';
import { ETaskPerformerType } from '../../../../types/template';
import type { EUserStatus, TUserListItem } from '../../../../types/user';

export enum EOptionTypes {
  Group = ETaskPerformerType.UserGroup,
  User = ETaskPerformerType.User,
  Starter = ETaskPerformerType.WorkflowStarter,
  Field = ETaskPerformerType.OutputUser,
  Manager = ETaskPerformerType.Manager,
  InviteUsers = 'invite-users',
  AllUsers = 'all-users',
}

export interface IGroupDropdownOption extends Omit<IGroup, 'type'> {
  optionType: EOptionTypes.Group;
  label: string;
  value: string;
  type: ETaskPerformerType.UserGroup;
}

export type TUsersDropdownOption = TDropdownOptionBase & {
  firstName?: string;
  lastName?: string;
  email?: string;
  status?: EUserStatus;
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
