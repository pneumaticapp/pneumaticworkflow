import * as React from 'react';
import { useMemo, useRef } from 'react';
import { useSelector } from 'react-redux';

import { ITaskFormProps } from './types';

import { getSystemVariables, getTaskVariables, getVariables } from './utils/getTaskVariables';
import { TaskFormHeader } from './TaskFormHeader';
import { TaskFormSections } from './TaskFormSections';
import { TaskFormScopeProvider, useTemplateField } from '../useTemplateForm';
import { getAccountId, getIsUserSubsribed } from '../../../redux/selectors/user';
import { getIsTeamInvitesModalOpen } from '../../../redux/selectors/team';

import styles from '../TemplateEdit.css';

export function TaskForm({
  task,
  users,
  scrollTarget,
}: ITaskFormProps) {
  const isSubscribed = useSelector(getIsUserSubsribed);
  const accountId = useSelector(getAccountId);
  const isTeamInvitesModalOpen = useSelector(getIsTeamInvitesModalOpen);
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
