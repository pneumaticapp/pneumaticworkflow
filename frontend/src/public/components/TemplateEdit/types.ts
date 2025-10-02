import React from 'react';
import { EExtraFieldType, IExtraFieldSelection } from '../../types/template';
import { TDropdownOptionBase } from '../UI/DropdownList';
import { EStartingType } from './TaskForm/Conditions/utils/getDropdownOperators';

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
  selections?: IExtraFieldSelection[];
};

export enum ETaskFormParts {
  CheckIf = 'checkIf',
  DueIn = 'dueIn',
  Fields = 'fields',
  AssignPerformers = 'assignPerformers',
  ReturnTo = 'returnTo',
  StartsAfter = 'startsAfter',
}

export type TTaskFormPart = ETaskFormParts | null;
