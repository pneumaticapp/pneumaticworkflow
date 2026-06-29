import * as React from 'react';
import { useMemo, useRef } from 'react';
import { FormikProvider, useFormik } from 'formik';

import { TUserListItem } from '../../../types/user';
import { IKickoff, ITemplateTask } from '../../../types/template';
import { TTaskVariable, TTaskFormPart } from '../types';
import { TPatchTaskPayload } from '../../../redux/actions';

import { getSystemVariables } from './utils/getTaskVariables';
import { TaskFormHeader } from './TaskFormHeader';
import { TaskFormSections } from './TaskFormSections';

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
  patchTask(args: TPatchTaskPayload): void;
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
  patchTask,
  templateId,
}: ITaskFormProps & { templateId: number | undefined }) {
  if (!task) return null;

  const wrapperRef = useRef<HTMLDivElement>(null);
  const formik = useFormik<ITemplateTask>({
    initialValues: task,
    enableReinitialize: true,
    onSubmit: () => undefined,
  });
  const currentTask = formik.values;
  const listSystemVariables = useMemo(() => [
    ...getSystemVariables(),
    ...listVariables,
  ], [listVariables]);

  const setCurrentTask = (changedFields: Partial<ITemplateTask>) => {
    Object.entries(changedFields).forEach(([field, value]) => formik.setFieldValue(field, value, false));
    patchTask({ taskUUID: currentTask.uuid, changedFields });
  };

  const handleTaskFieldChange = (field: keyof ITemplateTask) => (value: ITemplateTask[keyof ITemplateTask]) => {
    setCurrentTask({ [field]: value });
  };

  return (
    <FormikProvider value={formik}>
      <div ref={wrapperRef} className={styles['task_form']}>
        <div className={styles['task_form-popover']}>
          <TaskFormHeader
            accountId={accountId}
            currentTask={currentTask}
            handleTaskFieldChange={handleTaskFieldChange}
            listSystemVariables={listSystemVariables}
            templateVariables={templateVariables}
          />

          <TaskFormSections
            accountId={accountId}
            currentTask={currentTask}
            handleTaskFieldChange={handleTaskFieldChange}
            isSubscribed={isSubscribed}
            isTeamInvitesModalOpen={isTeamInvitesModalOpen}
            kickoff={kickoff}
            listVariables={listVariables}
            scrollTarget={scrollTarget}
            setCurrentTask={setCurrentTask}
            tasks={tasks}
            templateId={templateId}
            users={users}
            wrapperRef={wrapperRef}
          />
        </div>
      </div>
    </FormikProvider>
  );
}
