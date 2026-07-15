import React, { ComponentType, useCallback, useEffect, useMemo } from 'react';
import { useIntl } from 'react-intl';

import { ETaskFormParts, TTaskVariable } from '../types';
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
import { useTaskForm } from './useTaskForm';
import { ITaskFormPart, IUseTaskFormPartsProps, IWidgetProps } from './types';

import styles from '../TemplateEdit.css';

export function useTaskFormParts({
  accountId,
  isSubscribed,
  isTeamInvitesModalOpen,
  kickoff,
  listVariables,
  isFieldsSectionShown,
  tasks,
  templateId,
  users,
}: IUseTaskFormPartsProps): ITaskFormPart[] {
  const { formatMessage } = useIntl();
  const { task, updateTask, updateField } = useTaskForm();
  const startingOrder: TTaskVariable[] = useMemo(() => [
    {
      title: formatMessage({ id: 'templates.conditions.starting-order.kick-off' }),
      apiName: 'kick-off',
      type: EStartingType.Kickoff,
    },
    ...tasks
      .filter((localTask) => task.apiName !== localTask.apiName)
      .map((localTask) => ({
        apiName: localTask.apiName,
        title: localTask.name,
        type: EStartingType.Task,
        richSubtitle: <StepName initialStepName={localTask.name} templateId={templateId || 0} />,
      })),
  ], [task.apiName, formatMessage, tasks, templateId]);

  const onRemoveDeletedTasks = useCallback(
    (conditions: ICondition[]) => {
      updateTask({ conditions });
    },
    [updateTask],
  );

  useEffect(() => {
    removeDeletedTasks(startingOrder, task.conditions, onRemoveDeletedTasks);
  }, [startingOrder, task.conditions, onRemoveDeletedTasks]);

  const createWidget = useCallback(
    (
      Component: ComponentType<IWidgetProps & { onClick: () => void }>,
      { task: widgetTask, isInTaskForm, isStartTask }: IWidgetProps,
    ) => {
      return (toggle: () => void) => (
        <Component
          task={widgetTask}
          onClick={toggle}
          isInTaskForm={isInTaskForm}
          isStartTask={isStartTask}
        />
      );
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
          tasks={tasks}
          variables={listVariables}
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
            onChange={updateField('rawDueDate')}
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
          onOutputChange={updateField('fields')}
          isDisabled={false}
          show={isFieldsSectionShown}
          accountId={accountId}
        />
      ),
      widget: createWidget(TaskRenderExtraFieldsInfo, { task }),
    },
    {
      formPartId: ETaskFormParts.StartsAfter,
      title: 'templates.starts-after.title',
      component: (
        <StartAfterCondition
          isSubscribed={isSubscribed}
          conditions={task.conditions}
          startingOrder={startingOrder}
          variables={listVariables}
          users={users}
          onEdit={updateField('conditions')}
        />
      ),
      widget: createWidget(TaskRenderConditionsInfo, {
        task,
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
          conditions={task.conditions}
          startingOrder={startingOrder}
          variables={listVariables}
          users={users}
          onEdit={updateField('conditions')}
        />
      ),
      widget: createWidget(TaskRenderConditionsInfo, { task, isInTaskForm: true, isStartTask: false }),
    },
    {
      formPartId: ETaskFormParts.ReturnTo,
      title: 'templates.return-to.title',
      component: (
        <ReturnTo
          variables={listVariables}
          tasks={tasks}
          taskAncestors={new Set(task.ancestors)}
        />
      ),
      widget: createWidget(TaskRenderReturnInfo, { task }),
    },
  ];
}
