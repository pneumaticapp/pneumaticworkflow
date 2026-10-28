import type { ISelectProps, TSelectOption } from '../../Select';
import type { EUserStatus, TUserListItem } from '../../../../types/user';
import { ETaskPerformerType } from '../../../../types/template';

export enum EOptionTypes {
  Group = ETaskPerformerType.UserGroup,
  User = ETaskPerformerType.User,
  Starter = ETaskPerformerType.WorkflowStarter,
  Field = ETaskPerformerType.OutputUser,
  Manager = ETaskPerformerType.Manager,
  InviteUsers = 'invite-users',
  AllUsers = 'all-users',
}

export type TUsersDropdownOption = TSelectOption & {
  firstName?: string;
  lastName?: string;
  email?: string;
  status?: EUserStatus;
  id: number;
  optionType: EOptionTypes;
};

export interface IUsersDropdownProps<TOption extends TUsersDropdownOption> extends ISelectProps<TOption> {
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
