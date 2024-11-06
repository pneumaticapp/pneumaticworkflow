import React, { useEffect } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import Switch from 'rc-switch';

import {
  EWorkflowLogAttachmentsModes,
  EWorkflowsLogSorting,
  EWorkflowLogEvent,
  TWorkflowTask,
  IWorkflowLogItem,
  EWorkflowStatus,
} from '../../../types/workflow';
import { IChangeWorkflowLogViewSettingsPayload, ISendWorkflowLogComment } from '../../../redux/actions';
import { IntlMessages } from '../../IntlMessages';
import { isArrayWithItems } from '../../../utils/helpers';
import { PopupCommentFieldContainer } from './PopupCommentField';
import { workflowLogSortingValues } from '../../../constants/sortings';
import { SelectMenu, Tabs } from '../../UI';

import {
  WorkflowLogTaskComplete,
  WorkflowLogTaskSkipped,
  WorkflowLogTaskStart,
  WorkflowLogDelay,
  WorkflowLogProcessReturn,
  WorkflowLogWorkflowEndedOnCondition,
  WorkflowUrgent,
  WorkflowSkippedTask,
  WorkflowLogAddedPerformer,
  WorkflowLogRemovedPerformer,
  WorkflowLogWorkflowFinished,
  WorkflowLogTaskCommentContainer,
} from './WorkflowLogEvents';
import { WorkflowLogSkeleton } from './WorkflowLogSkeleton';
import { WorkflowLogWorkflowSnoozedManually } from './WorkflowLogEvents/WorkflowLogWorkflowSnoozedManually';
import { WorkflowLogWorkflowResumed } from './WorkflowLogEvents/WorkflowLogWorkflowResumed';
import { WorkflowLogDueDateChanged } from './WorkflowLogEvents/WorkflowLogDueDateChanged';

import styles from './WorkflowLog.css';

export const WorkflowLog = ({
  theme,
  items,
  sorting,
  isCommentsShown,
  isCommentFieldHidden,
  isOnlyAttachmentsShown,
  workflowId,
  includeHeader,
  currentTask,
  isLogMinimized,
  isLoading,
  minimizedLogMaxEvents,
  areTasksClickable,
  isToggleCommentHidden,
  workflowStatus,
  changeWorkflowLogViewSettings,
  sendComment,
  onClickTask,
  onUnmount,
}: IWorkflowLogProps) => {
  const { formatMessage } = useIntl();

  useEffect(() => {
    return () => {
      if (onUnmount) {
        onUnmount();
      }
    };
  }, []);

  const renderControls = () => {
    const activeAttachmentsMode = isOnlyAttachmentsShown
      ? EWorkflowLogAttachmentsModes.Attachments
      : EWorkflowLogAttachmentsModes.Timeline;

    if (!includeHeader) {
      return null;
    }

    return (
      <div className={styles['popup-body-controls']}>
        <div className={styles['popup-body-controls__inner']}>
          <div className={styles['popup-body-controls-general']}>
            <Tabs
              activeValueId={activeAttachmentsMode}
              values={[
                {
                  id: EWorkflowLogAttachmentsModes.Timeline,
                  label: formatMessage({id: 'sorting.timeline'}),
                },
                {
                  id: EWorkflowLogAttachmentsModes.Attachments,
                  label: formatMessage({id: 'sorting.attachments'}),
                },
              ]}
              onChange={toggleAttachments}
              containerClassName={classnames(
                styles['popup-body-controls-general__item'],
                theme === 'beige' && styles['popup-body-controls-general__item_beige'],
              )}
            />
            <SelectMenu
              values={workflowLogSortingValues}
              onChange={changeSorting}
              activeValue={sorting}
              containerClassName={classnames(
                styles['popup-body-controls-general__item'],
                theme === 'beige' && styles['popup-body-controls-general__item_beige'],
              )}
            />
          </div>
          {!isToggleCommentHidden && (
            <div className={styles['switch-container']}>
              <IntlMessages id="workflows.log-comments">
                {(text) => <span className={styles['switch-container__label']}>{text}</span>}
              </IntlMessages>
              <Switch
                className={classnames(
                  'custom-switch custom-switch-primary custom-switch-small',
                  styles['switch-container__button'],
                )}
                checkedChildren={null}
                unCheckedChildren={null}
                checked={isCommentsShown}
                onChange={toggleComments}
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  const toggleComments = () => {
    if (workflowId) {
      changeWorkflowLogViewSettings({ id: workflowId, sorting, comments: !isCommentsShown, isOnlyAttachmentsShown });
    }
  };

  const toggleAttachments = () => {
    if (workflowId) {
      changeWorkflowLogViewSettings({
        id: workflowId,
        sorting,
        comments: isCommentsShown,
        isOnlyAttachmentsShown: !isOnlyAttachmentsShown,
      });
    }
  };

  const changeSorting = () => {
    const newSorting = sorting === EWorkflowsLogSorting.New ? EWorkflowsLogSorting.Old : EWorkflowsLogSorting.New;

    if (workflowId) {
      changeWorkflowLogViewSettings({
        id: workflowId,
        sorting: newSorting,
        comments: isCommentsShown,
        isOnlyAttachmentsShown,
      });
    }
  };

  const renderCommentField = () => {
    if (
      isCommentFieldHidden ||
      isOnlyAttachmentsShown ||
      !isCommentsShown ||
      workflowStatus === EWorkflowStatus.Finished
    ) {
      return null;
    }

    return (
      <div className={styles['comment-field']}>
        <PopupCommentFieldContainer sendComment={sendComment} />
      </div>
    );
  };

  const renderWorkflowLogEvents = () => {
    if (!isArrayWithItems(items)) {
      return (
        <div className={styles['popup-body__no-events']}>
          <IntlMessages id="workflows.log-no-events" />
        </div>
      );
    }

    if (isLoading) {
      return <WorkflowLogSkeleton />;
    }

    const normalizedItems = isLogMinimized && minimizedLogMaxEvents ? items.slice(0, minimizedLogMaxEvents) : items;

    return normalizedItems.map((event) => {
      const { task: eventTask, type: eventType, delay, id } = event;

      const eventsMap = {
        [EWorkflowLogEvent.TaskStart]: (
          <WorkflowLogTaskStart
            theme={theme}
            onClickTask={onClickTask}
            logItems={items}
            sorting={sorting}
            currentTask={currentTask}
            areTasksClickable={areTasksClickable}
            {...event}
          />
        ),
        [EWorkflowLogEvent.TaskSkipped]: <WorkflowLogTaskSkipped theme={theme} {...event} />,
        [EWorkflowLogEvent.TaskComplete]: (
          <WorkflowLogTaskComplete currentTask={eventTask} isOnlyAttachmentsShown={isOnlyAttachmentsShown} {...event} />
        ),
        [EWorkflowLogEvent.WorkflowFinished]: <WorkflowLogWorkflowFinished {...event} />,
        [EWorkflowLogEvent.WorkflowSnoozed]: <WorkflowLogDelay delay={delay} theme={theme} />,
        [EWorkflowLogEvent.WorkflowSnoozedManually]: <WorkflowLogWorkflowSnoozedManually {...event} delay={delay!} />,
        [EWorkflowLogEvent.WorkflowResumed]: <WorkflowLogWorkflowResumed {...event} />,
        [EWorkflowLogEvent.WorkflowsReturned]: <WorkflowLogProcessReturn {...event} />,
        [EWorkflowLogEvent.TaskRevert]: <WorkflowLogProcessReturn {...event} />,
        [EWorkflowLogEvent.TaskComment]: (
          <WorkflowLogTaskCommentContainer
            workflowStatus={workflowStatus}
            isOnlyAttachmentsShown={isOnlyAttachmentsShown}
            {...event}
          />
        ),
        [EWorkflowLogEvent.WorkflowEndedOnCondition]: <WorkflowLogWorkflowEndedOnCondition {...event} />,
        [EWorkflowLogEvent.WorkflowIsUrgent]: <WorkflowUrgent {...event} />,
        [EWorkflowLogEvent.WorkflowIsNotUrgent]: <WorkflowUrgent isNotUrgent {...event} />,
        [EWorkflowLogEvent.TaskSkippedDueLackAssignedPerformers]: (
          <WorkflowSkippedTask
            theme={theme}
            onClickTask={onClickTask}
            areTasksClickable={areTasksClickable}
            {...event}
          />
        ),
        [EWorkflowLogEvent.AddedPerformer]: <WorkflowLogAddedPerformer {...event} />,
        [EWorkflowLogEvent.RemovedPerformer]: <WorkflowLogRemovedPerformer {...event} />,
        [EWorkflowLogEvent.DueDateChanged]: <WorkflowLogDueDateChanged {...event} />,
        [EWorkflowLogEvent.WorkflowComplete]: null,
        [EWorkflowLogEvent.WorkflowRun]: null,
      };

      return (
        <div key={`workflow-log-item-${id}`} className={styles['process-log-item']}>
          {eventsMap[eventType]}
        </div>
      );
    });
  };

  return (
    <div>
      {renderControls()}
      {renderCommentField()}
      <div>{renderWorkflowLogEvents()}</div>
    </div>
  );
};

export type TWorkflowLogTheme = 'white' | 'beige';

export interface IWorkflowLogProps {
  theme: TWorkflowLogTheme;
  items: IWorkflowLogItem[];
  sorting: EWorkflowsLogSorting;
  isCommentsShown: boolean;
  isCommentFieldHidden?: boolean;
  isOnlyAttachmentsShown: boolean;
  workflowId: number | null;
  includeHeader: boolean;
  workflowStatus: EWorkflowStatus;
  currentTask?: TWorkflowTask;
  isLogMinimized?: boolean;
  isLoading?: boolean;
  minimizedLogMaxEvents?: number;
  areTasksClickable?: boolean;
  isToggleCommentHidden?: boolean;
  changeWorkflowLogViewSettings(payload: IChangeWorkflowLogViewSettingsPayload): void;
  sendComment({ text, attachments }: ISendWorkflowLogComment): void;
  onClickTask?(): void;
  onUnmount?(): void;
}
