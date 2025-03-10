import React from 'react';
import { EExtraFieldType, IExtraFieldSelection } from '../../types/template';
import { TDropdownOptionBase } from '../UI/DropdownList';

export const enum ECustomResponsibleUsers {
  ProcessStarter = 'process-starter',
  InviteNewUserSelectorValue = 'invite-new-user-selector-option',
}

export interface ITemplateOwnerOption extends TDropdownOptionBase {
  id: number;
}

export type TTaskVariable = {
  title: string;
  subtitle: string;
  richSubtitle: React.ReactNode;
  apiName: string;
  type: EExtraFieldType;
  selections?: IExtraFieldSelection[];
};

export enum ETaskFormParts {
  Conditions = 'conditions',
  DueIn = 'dueIn',
  Fields = 'fields',
  AssignPerformers = 'assignPerformers',
  ReturnTo = 'returnTo',
}

export type TTaskFormPart = ETaskFormParts | null;
