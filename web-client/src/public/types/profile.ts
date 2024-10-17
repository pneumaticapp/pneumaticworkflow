export enum ESettingsTabs {
  Profile = 'profile',
  AccountSettings = 'settings',
}

export type TPasswordFields = {
  confirmNewPassword: string;
  newPassword: string;
  oldPassword: string;
};
