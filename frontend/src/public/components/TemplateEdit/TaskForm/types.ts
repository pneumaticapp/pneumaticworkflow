import type { ReactNode, RefObject } from 'react';

import { IKickoff, ITemplateTask } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { ETaskFormParts, TTaskFormPart, TTaskVariable } from '../types';

export interface ITaskFormProps {
  task: ITemplateTask;
  users: TUserListItem[];
  scrollTarget: TTaskFormPart;
}

export interface ITaskFormHeaderProps {
  accountId: number;
  listSystemVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
}

export interface ITaskFormSectionsProps {
  accountId: number;
  isSubscribed: boolean;
  isTeamInvitesModalOpen: boolean;
  kickoff: IKickoff;
  listVariables: TTaskVariable[];
  scrollTarget: TTaskFormPart;
  tasks: ITemplateTask[];
  templateId: number | undefined;
  users: TUserListItem[];
  wrapperRef: RefObject<HTMLDivElement>;
}

export interface ITaskPerformersProps {
  tasks: ITemplateTask[];
  users: TUserListItem[];
  variables: TTaskVariable[];
  isTeamInvitesModalOpen: boolean;
}

export interface IUseTaskFormPartsProps {
  accountId: number;
  isSubscribed: boolean;
  isTeamInvitesModalOpen: boolean;
  kickoff: IKickoff;
  listVariables: TTaskVariable[];
  isFieldsSectionShown: boolean;
  tasks: ITemplateTask[];
  templateId: number | undefined;
  users: TUserListItem[];
}

export interface IWidgetProps {
  task: ITemplateTask;
  isInTaskForm?: boolean;
  isStartTask?: boolean;
}

export interface ITaskFormPart {
  formPartId: ETaskFormParts;
  title: string;
  component: ReactNode;
  widget(toggle: () => void): ReactNode;
}
