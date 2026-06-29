import * as React from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useIntl } from 'react-intl';

import { TUserListItem } from '../../../types/user';
import { IKickoff, ITemplateTask } from '../../../types/template';
import { TTaskVariable, ETaskFormParts } from '../types';
import { TPatchTaskPayload } from '../../../redux/actions';
import { OutputFormIntl } from '../OutputForm';
import { StepName } from '../../StepName';
import { TaskItemUsers } from '../TaskItem/TaskItemUsers';
import { TaskRenderDueIn } from '../TaskRenderDueInInfo';
import { TaskRenderConditionsInfo } from '../TaskRenderConditionsInfo';
import { TaskRenderExtraFieldsInfo } from '../TaskRenderExtraFieldsInfo';
import { TaskRenderReturnInfo } from '../TaskRenderReturnInfo';
import { DueDate } from './DueDate';
import { ReturnTo } from './ReturnTo';
import { TaskPerformers } from './TaskPerformers';
import { CheckIfConditions, ICondition, removeDeletedTasks, StartAfterCondition } from './Conditions';
import { EStartingType } from './Conditions/utils/getDropdownOperators';

import styles from '../TemplateEdit.css';

interface IUseTaskFormPartsProps {
  accountId: number;
  currentTask: ITemplateTask;
  isSubscribed: boolean;
  isTeamInvitesModalOpen: boolean;
  kickoff: IKickoff;
  listVariables: TTaskVariable[];
  isFieldsSectionShown: boolean;
  tasks: ITemplateTask[];
  templateId: number | undefined;
  users: TUserListItem[];
  handleTaskFieldChange(field: keyof ITemplateTask): (value: ITemplateTask[keyof ITemplateTask]) => void;
  patchTask(args: TPatchTaskPayload): void;
  setCurrentTask(changedFields: Partial<ITemplateTask>): void;
}

interface IWidgetProps {
  task: ITemplateTask;
  isInTaskForm?: boolean;
  isStartTask?: boolean;
}

export interface ITaskFormPart {
  formPartId: ETaskFormParts;
  title: string;
  component: React.ReactNode;
  widget(toggle: () => void): React.ReactNode;
}

export function useTaskFormParts({
  accountId,
  currentTask,
  handleTaskFieldChange,
  isSubscribed,
  isTeamInvitesModalOpen,
  kickoff,
  listVariables,
  patchTask,
  isFieldsSectionShown,
  setCurrentTask,
  tasks,
  templateId,
  users,
}: IUseTaskFormPartsProps): ITaskFormPart[] {
  const { formatMessage } = useIntl();
  const startingOrder: TTaskVariable[] = useMemo(() => [
    {
      title: formatMessage({ id: 'templates.conditions.starting-order.kick-off' }),
      apiName: 'kick-off',
      type: EStartingType.Kickoff,
    },
    ...tasks
      .filter((localTask) => currentTask.apiName !== localTask.apiName)
      .map((localTask) => ({
        apiName: localTask.apiName,
        title: localTask.name,
        type: EStartingType.Task,
        richSubtitle: <StepName initialStepName={localTask.name} templateId={templateId || 0} />,
      })),
  ], [currentTask.apiName, formatMessage, tasks, templateId]);

  const onEdit = useCallback(
    (conditions: ICondition[]) => {
      patchTask({ taskUUID: currentTask.uuid, changedFields: { conditions } });
    },
    [patchTask, currentTask.uuid],
  );

  useEffect(() => {
    removeDeletedTasks(startingOrder, currentTask.conditions, onEdit);
  }, [startingOrder, currentTask.conditions, onEdit]);

  const createWidget = useCallback(
    (Component: (props: IWidgetProps & { onClick: () => void }) => React.ReactNode, props: IWidgetProps) => {
      return (toggle: () => void) => Component({
        task: props.task,
        onClick: toggle,
        isInTaskForm: props.isInTaskForm,
        isStartTask: props.isStartTask,
      });
    },
    [],
  );

  return [
    {
      formPartId: ETaskFormParts.AssignPerformers,
      title: 'tasks.task-assign-help',
      component: (
        <TaskPerformers
          users={users}
          task={currentTask}
          tasks={tasks}
          variables={listVariables}
          setCurrentTask={setCurrentTask}
          isTeamInvitesModalOpen={isTeamInvitesModalOpen}
        />
      ),
      widget: createWidget(TaskItemUsers, { task: currentTask }),
    },
    {
      formPartId: ETaskFormParts.DueIn,
      title: 'tasks.task-due-date',
      component: (
        <div className={styles['task-fields-wrapper']}>
          <DueDate
            dueDate={currentTask.rawDueDate}
            onChange={handleTaskFieldChange('rawDueDate')}
            currentTask={currentTask}
            kickoff={kickoff}
            tasks={tasks}
          />
        </div>
      ),
      widget: createWidget(TaskRenderDueIn, { task: currentTask, isInTaskForm: true }),
    },
    {
      formPartId: ETaskFormParts.Fields,
      title: 'tasks.task-outputs-create-help',
      component: (
        <OutputFormIntl
          fields={currentTask.fields}
          onOutputChange={handleTaskFieldChange('fields')}
          isDisabled={false}
          show={isFieldsSectionShown}
          accountId={accountId}
        />
      ),
      widget: createWidget(TaskRenderExtraFieldsInfo, { task: currentTask }),
    },
    {
      formPartId: ETaskFormParts.StartsAfter,
      title: 'templates.starts-after.title',
      component: (
        <StartAfterCondition
          isSubscribed={isSubscribed}
          conditions={currentTask.conditions}
          startingOrder={startingOrder}
          variables={listVariables}
          users={users}
          onEdit={handleTaskFieldChange('conditions')}
        />
      ),
      widget: createWidget(TaskRenderConditionsInfo, {
        task: currentTask,
        isInTaskForm: true,
        isStartTask: true,
      }),
    },
    {
      formPartId: ETaskFormParts.CheckIf,
      title: 'templates.conditions.check-if-title',
      component: (
        <CheckIfConditions
          isSubscribed={isSubscribed}
          conditions={currentTask.conditions}
          startingOrder={startingOrder}
          variables={listVariables}
          users={users}
          onEdit={handleTaskFieldChange('conditions')}
        />
      ),
      widget: createWidget(TaskRenderConditionsInfo, { task: currentTask, isInTaskForm: true, isStartTask: false }),
    },
    {
      formPartId: ETaskFormParts.ReturnTo,
      title: 'templates.return-to.title',
      component: (
        <ReturnTo
          variables={listVariables}
          tasks={tasks}
          currentTaskRevertTask={currentTask.revertTask}
          setCurrentTask={setCurrentTask}
          taskAncestors={new Set(currentTask.ancestors)}
        />
      ),
      widget: createWidget(TaskRenderReturnInfo, { task: currentTask }),
    },
  ];
}
