import { ComponentProps, ReactNode } from 'react';
import { RouteComponentProps } from 'react-router-dom';

import { EExtraFieldType, ITemplate } from '../../types/template';
import { TDropdownOptionBase } from '../UI/DropdownList';
import { EStartingType } from './TaskForm/Conditions/utils/getDropdownOperators';
import { TemplateEntity } from './TemplateEntity';

export interface ITemplateEditParams {
  id: string;
}

export type TTemplateEditProps = RouteComponentProps<ITemplateEditParams>;

export type TTaskListItemProps = ComponentProps<typeof TemplateEntity> & { key: string };

export interface ITemplateEditLayoutProps {
  accessConditions: boolean;
  sortedTasks(): ITemplate['tasks'];
  getTaskListItem(task: ITemplate['tasks'][number], index: number, tasks: ITemplate['tasks']): TTaskListItemProps;
  handleAddTask(): void;
}

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
  richSubtitle?: ReactNode;
  selections?: string[];
  datasetId?: number | null;
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
