import type { ESettingsTabs } from '../../types/profile';

export interface IStoreProfile {
  isLoading?: boolean;
  settingsTab: ESettingsTabs;
}
