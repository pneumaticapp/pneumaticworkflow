import React, { useLayoutEffect, useRef } from 'react';
import { useIntl } from 'react-intl';

import { TaskDescriptionEditor } from './TaskDescriptionEditor';

import { scrollToElement } from '../../../utils/helpers';
import { TUserListItem } from '../../../types/user';
import { IKickoff, ITemplateTask } from '../../../types/template';
import { TTaskVariable, TTaskFormPart, ETaskFormParts } from '../types';
import { OutputFormIntl } from '../OutputForm';
import { ShowMore } from '../../UI/ShowMore';
import { TaskPerformers } from './TaskPerformers';
import { Conditions } from './Conditions';
import { InputWithVariables } from '../InputWithVariables';
import { TPatchTaskPayload } from '../../../redux/actions';

import { DueDate } from './DueDate';
import { getSingleLineVariables } from './utils/getTaskVariables';

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
}: ITaskFormProps) {
  const { formatMessage } = useIntl();

  if (!task) return null;

  const taskFormPartsRefs = {
    [ETaskFormParts.AssignPerformers]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.DueIn]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.Fields]: useRef<HTMLDivElement>(null),
    [ETaskFormParts.Conditions]: useRef<HTMLDivElement>(null),
  };

  useLayoutEffect(() => {
    const scrollTo = (scrollTarget && taskFormPartsRefs[scrollTarget]?.current) || wrapperRef.current;

    if (scrollTo) {
      scrollToElement(scrollTo);
    }
  }, []);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const taskName = task.name || '';

  const setCurrentTask = (changedFields: Partial<ITemplateTask>) => {
    patchTask({ taskUUID: task.uuid, changedFields });
  };

  const handleTaskFieldChange = (field: keyof ITemplateTask) => (value: ITemplateTask[keyof ITemplateTask]) => {
    setCurrentTask({ [field]: value });
  };

  const taskFormParts = [
    {
      formPartId: ETaskFormParts.AssignPerformers,
      title: 'tasks.task-assign-help',
      component: (
        <TaskPerformers
          users={users}
          task={task}
          variables={listVariables}
          setCurrentTask={setCurrentTask}
          isTeamInvitesModalOpen={isTeamInvitesModalOpen}
        />
      ),
    },
    {
      formPartId: ETaskFormParts.DueIn,
      title: 'tasks.task-due-date',
      component: (
        <div className={styles['task-fields-wrapper']}>
          <DueDate
            dueDate={task.rawDueDate}
            onChange={handleTaskFieldChange('rawDueDate')}
            currentTask={task}
            kickoff={kickoff}
            tasks={tasks}
          />
        </div>
      ),
    },
    {
      formPartId: ETaskFormParts.Fields,
      title: 'tasks.task-outputs-create-help',
      component: (
        <OutputFormIntl
          fields={task.fields}
          onOutputChange={handleTaskFieldChange('fields')}
          isDisabled={false}
          show={ETaskFormParts.Fields === scrollTarget}
          accountId={accountId}
        />
      ),
    },
    {
      formPartId: ETaskFormParts.Conditions,
      title: 'templates.conditions.title',
      component: (
        <Conditions
          isSubscribed={isSubscribed}
          conditions={task.conditions}
          variables={listVariables}
          users={users}
          onEdit={handleTaskFieldChange('conditions')}
        />
      ),
    },
  ];

  return (
    <div ref={wrapperRef} className={styles['task_form']}>
      <div className={styles['task_form-popover']}>
        <div className={styles['task-fields-wrapper']}>
          <InputWithVariables
            placeholder={formatMessage({ id: 'tasks.task-task-name-placeholder' })}
            listVariables={getSingleLineVariables(listVariables)}
            templateVariables={templateVariables}
            value={taskName}
            onChange={(value: string) => {
              handleTaskFieldChange('name')(value);

              return Promise.resolve(value);
            }}
            className={styles['task-name-field']}
            title={formatMessage({ id: 'tasks.task-task-name' })}
            toolipText={formatMessage({ id: 'tasks.task-description-button-tooltip' })}
            size="lg"
          />
          <TaskDescriptionEditor
            handleChange={(value: string) => {
              handleTaskFieldChange('description')(value);

              return Promise.resolve(value);
            }}
            handleChangeChecklists={handleTaskFieldChange('checklists')}
            value={task.description || ''}
            listVariables={listVariables}
            templateVariables={templateVariables}
            accountId={accountId}
          />
        </div>
        {taskFormParts.map(({ title, component, formPartId }, index) => (
          <ShowMore
            label={`${index + 1}. ${formatMessage({ id: title })}`}
            containerClassName={styles['task-accordion-container']}
            isInitiallyVisible={formPartId === scrollTarget}
            key={title}
            innerRef={taskFormPartsRefs[formPartId]}
          >
            {component}
          </ShowMore>
        ))}
      </div>
    </div>
  );
}
