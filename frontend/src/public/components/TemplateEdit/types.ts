import type { ITemplateKickoffClient, ITemplateTaskClient } from '../../types/template';
import type { EMoveDirections } from '../../types/workflow';
import type { TDropdownOptionBase } from '../UI/DropdownList/types';
import type { TGraphAddTaskIntent } from './TemplateGraphEditor/types';

export const enum ECustomResponsibleUsers {
  ProcessStarter = 'process-starter',
  InviteNewUserSelectorValue = 'invite-new-user-selector-option',
}

export interface ITemplateOwnerOption extends TDropdownOptionBase {
  id: number;
}

export enum ETaskFormParts {
  CheckIf = 'checkIf',
  DueIn = 'dueIn',
  Fields = 'fields',
  Fieldsets = 'fieldsets',
  AssignPerformers = 'assignPerformers',
  ReturnTo = 'returnTo',
  StartsAfter = 'startsAfter',
}

export type TTaskFormPart = ETaskFormParts | null;

export type TTemplateEditorExpandedState = Record<string, boolean>;

export interface ITemplateEditorController {
  sortedTasks: ITemplateTaskClient[];
  openedTasks: TTemplateEditorExpandedState;
  openedDelays: TTemplateEditorExpandedState;
  setKickoff(value: ITemplateKickoffClient): void;
  addTask(): void;
  addTaskBefore(targetTask: ITemplateTaskClient, previousTaskApiName?: string): void;
  addTaskFromGraph(intent: TGraphAddTaskIntent): string | null;
  removeTask(targetTask: ITemplateTaskClient): void;
  cloneTask(targetTask: ITemplateTaskClient): void;
  moveTask(from: number, direction: EMoveDirections): void;
  addDelay(targetTask: ITemplateTaskClient): void;
  editDelay(targetTask: ITemplateTaskClient, delay: string): void;
  deleteDelay(targetTask: ITemplateTaskClient): void;
  toggleTask(taskUuid: string): void;
  toggleDelay(taskUuid: string): void;
}
