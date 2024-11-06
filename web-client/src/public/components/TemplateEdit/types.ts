/* eslint-disable */
/* prettier-ignore */
import { EExtraFieldType, IExtraFieldSelection } from '../../types/template';
import { TDropdownOptionBase } from '../UI/DropdownList';
import React from 'react';

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
}

export type TTaskFormPart = ETaskFormParts | null;
