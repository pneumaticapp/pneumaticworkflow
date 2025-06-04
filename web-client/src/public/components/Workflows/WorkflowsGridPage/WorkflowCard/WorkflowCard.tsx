import React, { ReactNode, useCallback, useEffect, useState } from 'react';
import classnames from 'classnames';
import { IntlShape } from 'react-intl';

import { EWorkflowStatus, EWorkflowTaskStatus, IWorkflow, IWorkflowTaskItem } from '../../../../types/workflow';
import { RawPerformer } from '../../../../types/template';
import { getSnoozedUntilDate } from '../../../../utils/dateTime';
import { isArrayWithItems } from '../../../../utils/helpers';
import { WorkflowCardUsers } from '../../../WorkflowCardUsers';
import { EProgressbarColor, ProgressBar } from '../../../ProgressBar';
import { sanitizeText } from '../../../../utils/strings';
import { DateFormat } from '../../../UI/DateFormat';
import { TemplateName } from '../../../UI/TemplateName';
import { getWorkflowProgressColor } from '../../utils/getWorkflowProgressColor';
import { getWorkflowProgress } from '../../utils/getWorkflowProgress';
import { WorkflowControlls } from '../../WorkflowControlls';
import { Dropdown, Tooltip } from '../../../UI';
import { MoreIcon } from '../../../icons';
import { ProgressbarTooltipContents } from '../../utils/ProgressbarTooltipContents';

import styles from '../WorkflowsGridPage.css';

export interface IWorkflowCardProps {
  intl: IntlShape;
  workflow: IWorkflow;
  onCardClick(e: React.SyntheticEvent): void;
  onWorkflowEnded?(): void;
  onWorkflowSnoozed?(): void;
  onWorkflowDeleted?(): void;
  onWorkflowResumed?(): void;
}

export const WorkflowCard = ({
  intl: { formatMessage },
  workflow,
  onCardClick,
  onWorkflowEnded,
  onWorkflowSnoozed,
  onWorkflowDeleted,
  onWorkflowResumed,
}: IWorkflowCardProps) => {
  const [areOverdueTasks, setAreOverdueTasks] = useState(false);
  const [formattedTasks, setFormattedTasks] = useState<IWorkflowTaskItem[]>([]);
  const [areMultipleTasks, setAreMultipleTasks] = useState(false);
  const [namesTooltip, setNamesTooltip] = useState<ReactNode[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<RawPerformer[]>([]);

  const isCardPending = false;
  const {
    name: workflowName,
    activeCurrentTask,
    activeTasksCount,
    status,
    template,
    isLegacyTemplate,
    legacyTemplateName,
    task: { delay, name: taskName, dueDate: taskDueDate },
    isUrgent,
    dueDate,
    tasks,
    dateCompleted,
  } = workflow;

  const getStepColor = useCallback(
    (task: IWorkflowTaskItem) => {
      if (status === EWorkflowStatus.Snoozed && task.status !== EWorkflowTaskStatus.Pending) {
        return EProgressbarColor.Grey;
      }
      if (
        task.status === EWorkflowTaskStatus.Completed ||
        (status === EWorkflowStatus.Finished && task.status !== EWorkflowTaskStatus.Pending)
      ) {
        return EProgressbarColor.Green;
      }
      if (task.status === EWorkflowTaskStatus.Active) {
        return task.overdue ? EProgressbarColor.Red : EProgressbarColor.Yellow;
      }

      return undefined;
    },
    [status],
  );

  const checkOverdueTask = useCallback((task: IWorkflowTaskItem) => {
    const defaultResult = { isOverdue: false, count: 0 };
    if (!task.dueDateTsp) return defaultResult;

    const isOverdue = task.dueDateTsp < Date.now();
    if (isOverdue && task.status === EWorkflowTaskStatus.Active) {
      return { isOverdue: true, count: 1 };
    }
    if (task.overdue && task.status !== EWorkflowTaskStatus.Active) {
      return { isOverdue: false, count: -1 };
    }

    return defaultResult;
  }, []);

  const createTaskNameTooltips = useCallback(
    (taskNames: string[]) =>
      taskNames.map((name, index) => (
        <div key={name}>
          <div className={styles['card-tooltip-task-number']}>
            {`${formatMessage({ id: 'workflows.tasks' })} ${index + 1}`}
          </div>
          <div>{name}</div>
        </div>
      )),
    [formatMessage],
  );

  useEffect(() => {
    let overdueTasksCount = 0;
    let multipleTasksCount = 0;
    const namesMultipleTasks: string[] = [];
    const currentPerformersMap = new Map();

    const formattedTasksList = tasks.map((task) => {
      const newTask = { ...task };

      const { isOverdue, count } = checkOverdueTask(newTask);
      newTask.overdue = isOverdue;
      overdueTasksCount += count;
      newTask.color = getStepColor(newTask);

      if (newTask.status === EWorkflowTaskStatus.Active) {
        multipleTasksCount += 1;

        namesMultipleTasks.push(newTask.name);

        newTask.performers.forEach((performer) => {
          currentPerformersMap.set(performer.sourceId, performer);
        });
      }

      return newTask;
    });

    if (multipleTasksCount > 1) {
      setAreMultipleTasks(true);
      setNamesTooltip(createTaskNameTooltips(namesMultipleTasks));
    } else {
      setAreMultipleTasks(false);
      setNamesTooltip([]);
    }

    setSelectedUsers(Array.from(currentPerformersMap.values()));
    setFormattedTasks(formattedTasksList);
    setAreOverdueTasks(Boolean(overdueTasksCount));
  }, [tasks, status, formatMessage, checkOverdueTask, getStepColor, createTaskNameTooltips]);

  const progress = getWorkflowProgress({ activeCurrentTask, activeTasksCount, status });

  const getSnoozedText = () => {
    if (!delay) return '';

    return formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(delay) });
  };

  const renderCardFooter = () => {
    if (status !== EWorkflowStatus.Running) return null;
    return (
      <div className={styles['footer-users-and-links']}>
        <WorkflowCardUsers users={selectedUsers} />
      </div>
    );
  };

  const renderCardSubtitle = () => {
    const subtitlesMap = {
      [EWorkflowStatus.Running]: areMultipleTasks ? (
        <Tooltip content={namesTooltip}>
          <div>{formatMessage({ id: 'workflows.multiple-active-tasks' })}</div>
        </Tooltip>
      ) : (
        taskName
      ),
      [EWorkflowStatus.Snoozed]: getSnoozedText(),
      [EWorkflowStatus.Finished]:
        dateCompleted && formatMessage({ id: 'workflows.finished' }, { date: <DateFormat date={dateCompleted} /> }),
      [EWorkflowStatus.Aborted]: '',
    };

    return <div className={classnames(styles['card-task'], 'truncate')}>{subtitlesMap[status]}</div>;
  };

  return (
    <div className={styles['card-wrapper']}>
      <div
        role="button"
        tabIndex={0}
        className={classnames(
          styles['card'],
          isUrgent && styles['card-urgent'],
          isCardPending && styles['card-pending'],
          status === EWorkflowStatus.Finished && styles['card-process-finished'],
          areOverdueTasks &&
            status !== EWorkflowStatus.Finished &&
            status !== EWorkflowStatus.Snoozed &&
            styles['card-active-task-overdue'],
          (status !== EWorkflowStatus.Finished || !areOverdueTasks) && styles['card-process-based'],
        )}
        onClick={onCardClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onCardClick(e);
          }
        }}
      >
        {isCardPending && <div className={classnames(styles['loading'], 'loading')} />}

        <WorkflowControlls
          workflow={workflow}
          onWorkflowEnded={onWorkflowEnded}
          onWorkflowSnoozed={onWorkflowSnoozed}
          onWorkflowDeleted={onWorkflowDeleted}
          onWorkflowResumed={onWorkflowResumed}
        >
          {(controllOptions) => {
            if (!isArrayWithItems(controllOptions)) {
              return null;
            }

            return (
              <div className={styles['dropdown']}>
                <Dropdown
                  renderToggle={(isOpen) => (
                    <MoreIcon className={classnames(styles['card-more'], isOpen && styles['card-more_active'])} />
                  )}
                  options={controllOptions}
                />
              </div>
            );
          }}
        </WorkflowControlls>
        <TemplateName
          isLegacyTemplate={isLegacyTemplate}
          legacyTemplateName={legacyTemplateName}
          templateName={template?.name}
          className={styles['card-pretitle']}
        />
        <div className={styles['card-title']} title={sanitizeText(workflowName)}>
          {sanitizeText(workflowName)}
        </div>
        <div
          className={classnames(
            styles['card-footer'],
            (areOverdueTasks && status !== EWorkflowStatus.Snoozed) || status === EWorkflowStatus.Finished
              ? styles['card-footer-white']
              : styles['card-footer-base'],
          )}
        >
          <ProgressBar
            tasks={formattedTasks}
            progress={progress}
            background="white"
            color={getWorkflowProgressColor(status, [taskDueDate, dueDate])}
            containerClassName={styles['progress-bar-container']}
            tooltipContent={<ProgressbarTooltipContents workflow={workflow} />}
          />
          {renderCardSubtitle()}
          {renderCardFooter()}
        </div>
      </div>
    </div>
  );
};
