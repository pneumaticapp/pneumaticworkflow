import { TSystemField } from './types';

export const SYSTEM_FIELD_NAMES = [
  'system-column-workflow',
  'system-column-starter',
  'system-column-progress',
  'system-column-step',
  'system-column-performer',
];
export const ALL_SYSTEM_FIELD_NAMES = [
  'system-column-workflow',
  'system-column-templateName',
  'system-column-starter',
  'system-column-progress',
  'system-column-step',
  'system-column-performer',
];

export const SYSTEM_FIELDS: TSystemField[] = [
  { apiName: 'system-column-workflow', name: 'workflow', isDisabled: true, hasNotTooltip: true },
  { apiName: 'system-column-starter', name: 'starter', isDisabled: false, hasNotTooltip: true },
  { apiName: 'system-column-progress', name: 'progress', isDisabled: false, hasNotTooltip: true },
  { apiName: 'system-column-step', name: 'step', isDisabled: false, hasNotTooltip: true },
  { apiName: 'system-column-performer', name: 'performer', isDisabled: false, hasNotTooltip: true },
];

export const SKELETON_ROWS = Array.from({ length: 5 }, (_, index) => `skeleton-row-${index}`);
