import React from 'react';
import { EExtraFieldType, ITemplateKickoffClient, ITemplateTaskClient } from '../../types/template';
import { EMoveDirections } from '../../types/workflow';
import { TDropdownOptionBase } from '../UI/DropdownList';
import { EStartingType } from './TaskForm/Conditions/utils/getDropdownOperators';
import type { TGraphAddTaskIntent } from './TemplateGraphEditor/types';

export const enum ECustomResponsibleUsers {
  ProcessStarter = 'process-starter',
  InviteNewUserSelectorValue = 'invite-new-user-selector-option',
}

export interface ITemplateOwnerOption extends TDropdownOptionBase {
  id: number;
}

export type TTaskVariable = {
  title: string;
  apiName: string;
  type: EExtraFieldType | EStartingType;
  subtitle?: string;
  richSubtitle?: React.ReactNode;
  selections?: string[];
  datasetId?: number | null;
};

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
