import { TSystemField } from './types';

export const SYSTEM_FIELD_NAMES = ['workflow', 'starter', 'progress', 'step', 'performer'];
export const ALL_SYSTEM_FIELD_NAMES = ['workflow', 'templateName', 'starter', 'progress', 'step', 'performer'];

export const SYSTEM_FIELDS: TSystemField[] = [
  { apiName: 'workflow', name: 'workflow', isDisabled: true, hasNotTooltip: true },
  { apiName: 'starter', name: 'starter', isDisabled: false, hasNotTooltip: true },
  { apiName: 'progress', name: 'progress', isDisabled: false, hasNotTooltip: true },
  { apiName: 'step', name: 'step', isDisabled: false, hasNotTooltip: true },
  { apiName: 'performer', name: 'performer', isDisabled: false, hasNotTooltip: true },
];

export const SKELETON_ROWS = Array.from({ length: 5 }, (_, index) => `skeleton-row-${index}`);
