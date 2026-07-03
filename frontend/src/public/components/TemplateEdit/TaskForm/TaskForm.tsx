import * as React from 'react';
import { useMemo, useRef } from 'react';

import { TUserListItem } from '../../../types/user';
import { ITemplateTask } from '../../../types/template';
import { TTaskFormPart } from '../types';

import { getSystemVariables, getTaskVariables, getVariables } from './utils/getTaskVariables';
import { TaskFormHeader } from './TaskFormHeader';
import { TaskFormSections } from './TaskFormSections';
import { TaskFormScopeProvider, useTemplateField } from '../useTemplateForm';

import styles from '../TemplateEdit.css';

export interface ITaskFormProps {
  task: ITemplateTask;
  users: TUserListItem[];
  isSubscribed: boolean;
  scrollTarget: TTaskFormPart;
  accountId: number;
  isTeamInvitesModalOpen: boolean;
}

export function TaskForm({
  task,
  users,
  isSubscribed,
  accountId,
  scrollTarget,
  isTeamInvitesModalOpen,
}: ITaskFormProps) {
  if (!task) return null;

  const wrapperRef = useRef<HTMLDivElement>(null);
  // `kickoff`, `tasks`, and the variable lists are read from the Formik form
  // state rather than Redux. Field edits land in Formik first and only get
  // patched into Redux later (debounced by `TemplateFormPersistProvider`), so
  // reading from Redux here would render sections like conditions, due dates,
  // and return-to against stale task/kickoff data.
  const { values } = useTemplateField();
  const { kickoff, tasks, id: templateId } = values;

  const listVariables = useMemo(
    () => getTaskVariables(kickoff, tasks, task, templateId),
    [kickoff, tasks, task, templateId],
  );
  const templateVariables = useMemo(
    () => getVariables({ kickoff, tasks, templateId }),
    [kickoff, tasks, templateId],
  );
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
