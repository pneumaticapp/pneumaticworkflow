import * as React from 'react';
import { useMemo, useRef } from 'react';

import { TUserListItem } from '../../../types/user';
import { IKickoff, ITemplateTask } from '../../../types/template';
import { TTaskVariable, TTaskFormPart } from '../types';

import { getSystemVariables } from './utils/getTaskVariables';
import { TaskFormHeader } from './TaskFormHeader';
import { TaskFormSections } from './TaskFormSections';
import { TaskFormScopeProvider } from '../useTemplateForm';

import styles from '../TemplateEdit.css';

export interface ITaskFormProps {
  listVariables: TTaskVariable[];
  templateVariables: TTaskVariable[];
  task: ITemplateTask;
  users: TUserListItem[];
  isSubscribed: boolean;
  scrollTarget: TTaskFormPart;
  accountId: number;
  isTeamInvitesModalOpen: boolean;
  tasks: ITemplateTask[];
  kickoff: IKickoff;
}

export function TaskForm({
  listVariables,
  templateVariables,
  task,
  users,
  isSubscribed,
  accountId,
  scrollTarget,
  isTeamInvitesModalOpen,
  tasks,
  kickoff,
  templateId,
}: ITaskFormProps & { templateId: number | undefined }) {
  if (!task) return null;

  const wrapperRef = useRef<HTMLDivElement>(null);
  const listSystemVariables = useMemo(() => [
    ...getSystemVariables(),
    ...listVariables,
  ], [listVariables]);

  return (
    <TaskFormScopeProvider taskUuid={task.uuid}>
      <div ref={wrapperRef} className={styles['task_form']}>
        <div className={styles['task_form-popover']}>
          <TaskFormHeader
            accountId={accountId}
            listSystemVariables={listSystemVariables}
            templateVariables={templateVariables}
          />

          <TaskFormSections
            accountId={accountId}
            isSubscribed={isSubscribed}
            isTeamInvitesModalOpen={isTeamInvitesModalOpen}
            kickoff={kickoff}
            listVariables={listVariables}
            scrollTarget={scrollTarget}
            tasks={tasks}
            templateId={templateId}
            users={users}
            wrapperRef={wrapperRef}
          />
        </div>
      </div>
    </TaskFormScopeProvider>
  );
}
