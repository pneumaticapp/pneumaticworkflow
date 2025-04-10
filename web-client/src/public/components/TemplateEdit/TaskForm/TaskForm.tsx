import React, { useCallback, useLayoutEffect, useRef } from 'react';
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

import { ReturnTo } from './ReturnTo';
import { DueDate } from './DueDate';
import { getSingleLineVariables } from './utils/getTaskVariables';

import styles from '../TemplateEdit.css';
import { TaskItemUsers } from '../TaskItem/TaskItemUsers';
import { TaskRenderDueIn } from '../TaskRenderDueInInfo';
import { TaskRenderConditionsInfo } from '../TaskRenderConditionsInfo';
import { TaskRenderExtraFieldsInfo } from '../TaskRenderExtraFieldsInfo';
import { TaskRenderReturnInfo } from '../TaskRenderReturnInfo';

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
    [ETaskFormParts.ReturnTo]: useRef<HTMLDivElement>(null),
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

  const createWidget = useCallback(
    (Component, props) => {
      return (toggle: () => void) => <Component task={props.task} onClick={toggle} isInTaskForm={props.isInTaskForm} />;
    },
    [task],
  );

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
      widget: createWidget(TaskItemUsers, { task }),
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
      widget: createWidget(TaskRenderDueIn, { task, isInTaskForm: true }),
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
      widget: createWidget(TaskRenderExtraFieldsInfo, { task }),
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
      widget: createWidget(TaskRenderConditionsInfo, { task, isInTaskForm: true }),
    },
    {
      formPartId: ETaskFormParts.ReturnTo,
      title: 'templates.return-to.title',
      component: (
        <ReturnTo
          variables={listVariables}
          tasks={tasks}
          currentTaskRevertTask={task.revertTask}
          currentTaskApiName={task.apiName}
          setCurrentTask={setCurrentTask}
        />
      ),
      widget: createWidget(TaskRenderReturnInfo, { task }),
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

        {taskFormParts.map(({ title, component, formPartId, widget }) => (
          <ShowMore
            isDisabled={title === 'templates.return-to.title' && tasks.length < 2}
            label={formatMessage({ id: title })}
            containerClassName={styles['task-accordion-container']}
            isInitiallyVisible={formPartId === scrollTarget}
            key={title}
            innerRef={taskFormPartsRefs[formPartId]}
            widget={widget}
          >
            {component}
          </ShowMore>
        ))}
      </div>
    </div>
  );
}
