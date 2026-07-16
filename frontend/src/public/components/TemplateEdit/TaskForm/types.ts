import type { ReactNode, RefObject } from 'react';

import { IKickoffClient, ITemplateTaskClient } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { ETaskFormParts, TTaskFormPart, TTaskVariable } from '../types';

export interface ITaskFormProps {
  task: ITemplateTaskClient;
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
  kickoff: IKickoffClient;
  listVariables: TTaskVariable[];
  scrollTarget: TTaskFormPart;
  tasks: ITemplateTaskClient[];
  templateId: number | undefined;
  users: TUserListItem[];
  wrapperRef: RefObject<HTMLDivElement>;
}

export interface ITaskPerformersProps {
  tasks: ITemplateTaskClient[];
  users: TUserListItem[];
  variables: TTaskVariable[];
  isTeamInvitesModalOpen: boolean;
}

export interface IUseTaskFormPartsProps {
  accountId: number;
  isSubscribed: boolean;
  isTeamInvitesModalOpen: boolean;
  kickoff: IKickoffClient;
  listVariables: TTaskVariable[];
  isFieldsSectionShown: boolean;
  tasks: ITemplateTaskClient[];
  templateId: number | undefined;
  users: TUserListItem[];
}

export interface IWidgetProps {
  task: ITemplateTaskClient;
  isInTaskForm?: boolean;
  isStartTask?: boolean;
}

export interface ITaskFormPart {
  formPartId: ETaskFormParts;
  title: string;
  component: ReactNode;
  widget(toggle: () => void): ReactNode;
}
