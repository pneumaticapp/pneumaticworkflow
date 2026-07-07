import { ETaskFormParts } from '../types';

export type TTemplateValidationScrollTarget =
  | { area: 'name' }
  | { area: 'owners' }
  | { area: 'kickoff'; fieldApiName?: string }
  | { area: 'tasks' }
  | { area: 'task'; taskUuid: string; formPart: ETaskFormParts; fieldApiName?: string; ruleApiName?: string };

export type TTemplateValidationError = {
  path: string;
  messageId: string;
  scrollTarget: TTemplateValidationScrollTarget;
};

export type TTemplateValidationResult = {
  blockingErrors: TTemplateValidationError[];
  infoWarnings: ((props: import('../InfoWarningsModal/warnings').IInfoWarningProps) => JSX.Element)[];
};
