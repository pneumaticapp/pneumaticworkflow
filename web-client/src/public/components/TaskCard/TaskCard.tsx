import React, { useEffect, useState, useRef } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { Link } from 'react-router-dom';
import { debounce } from 'throttle-debounce';
import { useSelector } from 'react-redux';

import { autoFocusFirstField } from '../../utils/autoFocusFirstField';
import { EExtraFieldMode, ETaskPerformerType, ETemplateOwnerType, IExtraField } from '../../types/template';
import { sanitizeText } from '../../utils/strings';
import { ITask } from '../../types/tasks';
import {
  ETaskStatus,
  IChangeWorkflowLogViewSettingsPayload,
  ISendWorkflowLogComment,
  TAddTaskPerformerPayload,
  TOpenModalPayload,
  TOpenWorkflowLogPopupPayload,
  TRemoveTaskPerformerPayload,
  TSetTaskCompletedPayload,
  TSetTaskRevertedPayload,
  TSetWorkflowFinishedPayload,
} from '../../redux/actions';
import { ExtraFieldsHelper } from '../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getTaskDetailRoute, getWorkflowDetailedRoute, isTaskDetailRoute } from '../../utils/routes';
import { Header } from '../UI/Typeography/Header';
import { RichText } from '../RichText';
import { getUserFullName } from '../../utils/users';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';
import { isArrayWithItems, isEmptyArray } from '../../utils/helpers';
import { useCheckDevice } from '../../hooks/useCheckDevice';
import { history } from '../../utils/history';
import {
  EInputNameBackgroundColor,
  EWorkflowsLogSorting,
  EWorkflowStatus,
  IWorkflowDetails,
} from '../../types/workflow';
import { getEditedFields } from '../TemplateEdit/ExtraFields/utils/getEditedFields';
import { IntlMessages } from '../IntlMessages';
import { Button } from '../UI/Buttons/Button';
import { IApplicationState, IAuthUser, IWorkflowLog } from '../../types/redux';
import { WorkflowLog } from '../Workflows/WorkflowLog';
import { DoneInfoIcon, PlayLogoIcon, ReturnTaskInfoIcon, ReturnToIcon } from '../icons';
import { WorkflowLogSkeleton } from '../Workflows/WorkflowLog/WorkflowLogSkeleton';
import { EOptionTypes, TUsersDropdownOption, UsersDropdown } from '../UI/form/UsersDropdown';
import { TUserListItem } from '../../types/user';
import { trackInviteTeamInPage } from '../../utils/analytics';
import { Tooltip } from '../UI';
import { addOrUpdateStorageOutput, getOutputFromStorage } from './utils/storageOutputs';
import { TaskCarkSkeleton } from './TaskCarkSkeleton';
import { GuestController } from './GuestsController';
import { createChecklistExtension, createProgressbarExtension } from './checklist';
import { DueIn } from '../DueIn';
import { SubWorkflowsContainer } from './SubWorkflows';
import { EBgColorTypes, UserPerformer } from '../UI/UserPerformer';
import { DateFormat } from '../UI/DateFormat';
import UserDataWithGroup from '../UserDataWithGroup';

import styles from './TaskCard.css';
import { ReturnModal } from './ReturnModal';

export enum ETaskCardViewMode {
  Single = 'single',
  List = 'list',
  Guest = 'guest',
}

const MINIMIZED_LOG_MAX_EVENTS = 5;

export interface ITaskCardProps {
  task: ITask;
  viewMode: ETaskCardViewMode;
  workflowLog: IWorkflowLog;
  workflow: IWorkflowDetails | null;
  status: ETaskStatus;
  isWorkflowLoading: boolean;
  accountId: number;
  users: TUserListItem[];
  authUser: IAuthUser;
  addTaskPerformer(payload: TAddTaskPerformerPayload): void;
  removeTaskPerformer(payload: TRemoveTaskPerformerPayload): void;
  changeTaskWorkflowLog(value: Partial<IWorkflowLog>): void;
  setTaskCompleted(payload: TSetTaskCompletedPayload): void;
  setTaskReverted(payload: TSetTaskRevertedPayload): void;
  setWorkflowFinished(payload: TSetWorkflowFinishedPayload): void;
  sendTaskWorkflowLogComments(payload: ISendWorkflowLogComment): void;
  changeTaskWorkflowLogViewSettings(payload: IChangeWorkflowLogViewSettingsPayload): void;
  setCurrentTask(task: ITask | null): void;
  clearWorkflow(): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
  setDueDate(date: string): void;
  deleteDueDate(): void;
  openSelectTemplateModal(payload: TOpenModalPayload): void;
}

export function TaskCard({
  task,
  viewMode,
  workflowLog,
  workflow,
  isWorkflowLoading,
  status,
  accountId,
  users,
  authUser,
  changeTaskWorkflowLog,
  setCurrentTask,
  setTaskCompleted,
  setTaskReverted,
  sendTaskWorkflowLogComments,
  changeTaskWorkflowLogViewSettings,
  clearWorkflow,
  addTaskPerformer,
  removeTaskPerformer,
  openWorkflowLogPopup,
  setDueDate,
  deleteDueDate,
  openSelectTemplateModal,
}: ITaskCardProps) {
  const { formatMessage } = useIntl();
  const { isMobile } = useCheckDevice();

  const groups = useSelector((state: IApplicationState) => state.groups.list);
  const saveOutputsToStorageDebounced = debounce(300, addOrUpdateStorageOutput);

  const guestsControllerRef = useRef<React.ElementRef<typeof GuestController> | null>(null);
  const wrapperRef = useRef(null);
  const workflowLinkRef = useRef(null);
  const [outputValues, setOutputValues] = useState([] as IExtraField[]);
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);

  useEffect(() => {
    autoFocusFirstField(wrapperRef.current);

    return () => {
      setCurrentTask(null);
      clearWorkflow();
    };
  }, []);

  useEffect(() => {
    guestsControllerRef.current?.updateDropdownPosition();
  }, [task.performers.length]);

  useEffect(() => {
    const { output, id } = task;
    const storageOutput = getOutputFromStorage(id);
    const outputFieldsWithValues = new ExtraFieldsHelper(output, storageOutput).getFieldsWithValues();

    setOutputValues(outputFieldsWithValues);
  }, [task.id]);

  const handleOpenWorkflowPopup = (workflowId: number | null) => (e: React.MouseEvent) => {
    e.preventDefault();
    if (workflowId) {
      openWorkflowLogPopup({ workflowId });
    }
  };

  const handleDelegateWorkflow = () => {
    openSelectTemplateModal({
      ancestorTaskId: task.id,
    });
  };

  const renderHeader = () => {
    const {
      name,
      id,
      dateStarted,
      workflow: { name: workflowName, templateName },
      isUrgent,
    } = task;
    const redirectToWorkflowUrl = workflowLog?.workflowId ? getWorkflowDetailedRoute(workflowLog.workflowId) : '#';
    const redirectToTaskUrl = getTaskDetailRoute(id);
    const showLinkToTaskDetail = !isTaskDetailRoute(history.location.pathname);

    if (viewMode === ETaskCardViewMode.Guest) {
      return (
        <Header size="4" tag="h1" className={styles['guest-task-name']}>
          {name}
        </Header>
      );
    }

    return (
      <>
        <div className={styles['pretitle']}>
          {templateName}
          <div className={styles.dot} />
          <Tooltip
            content={formatMessage({ id: 'workflows.name' })}
            containerClassName={styles['workflow-name-container']}
          >
            <span>
              <Link
                innerRef={workflowLinkRef}
                to={redirectToWorkflowUrl}
                onClick={handleOpenWorkflowPopup(workflowLog.workflowId)}
                className={styles['workflow-name']}
              >
                {sanitizeText(workflowName)}
              </Link>
            </span>
          </Tooltip>
        </div>

        <div className={styles['task-name-container']}>
          <Header size="4" tag="h4">
            {isUrgent ? (
              <div className={styles['task-name__urgent-marker']}>{formatMessage({ id: 'workflows.card-urgent' })}</div>
            ) : null}
            {showLinkToTaskDetail ? <Link to={redirectToTaskUrl}>{sanitizeText(name)}</Link> : sanitizeText(name)}
          </Header>
        </div>
        <span className={styles['date']}>
          <DateFormat date={dateStarted} />
        </span>
      </>
    );
  };

  const renderPerformers = () => {
    const isPossibleToRemovePerformer = [
      task.performers.length > 1,
      viewMode !== ETaskCardViewMode.Guest,
      status !== ETaskStatus.Completed,
      workflow?.status !== EWorkflowStatus.Finished,
    ].every(Boolean);

    return task.performers.map((performer) => {
      return (
        <UserDataWithGroup key={performer.sourceId} idItem={performer.sourceId} type={performer.type}>
          {(user) => {
            return (
              <UserPerformer
                user={{
                  ...user,
                  sourceId: String(user.id),
                  value: String(user.id),
                  label: getUserFullName(user),
                }}
                bgColor={EBgColorTypes.Light}
                {...(isPossibleToRemovePerformer && {
                  onClick: () => removeTaskPerformer({ taskId: task.id, userId: performer }),
                })}
              />
            );
          }}
        </UserDataWithGroup>
      );
    });
  };

  const renderPerformersControllers = () => {
    if (status === ETaskStatus.Completed || workflow?.status === EWorkflowStatus.Finished) return null;

    const performerDropdownOption = users.map((item) => {
      return {
        ...item,
        optionType: EOptionTypes.User,
        label: getUserFullName(item),
        value: String(item.id),
      };
    });

    const mapPerformersDropdownValue = users.filter((user) =>
      task.performers.find(({ sourceId }) => user.id === sourceId),
    );
    const performerDropdownValue = mapPerformersDropdownValue.map((item) => {
      return {
        ...item,
        optionType: EOptionTypes.User,
        label: getUserFullName(item),
        value: String(item.id),
      };
    });

    const performerGroupDropdownOption = groups.map((group) => {
      return {
        ...group,
        optionType: EOptionTypes.Group,
        type: ETaskPerformerType.UserGroup,
        label: group.name,
        value: String(group.id),
      };
    });

    const mapGroupDropdownValue = groups.filter((user) =>
      task.performers.find(({ sourceId }) => Number(sourceId) === user.id),
    );

    const performerGroupDropdownValue = mapGroupDropdownValue.map((group) => {
      return {
        ...group,
        optionType: EOptionTypes.Group,
        label: group.name,
        value: String(group.id),
      };
    });

    const onUsersInvited = (invitedUsers: TUserListItem[]) => {
      invitedUsers.forEach((user) =>
        addTaskPerformer({
          taskId: task.id,
          userId: {
            sourceId: user.id,
            type: ETemplateOwnerType.User,
          },
        }),
      );
    };

    const onRemoveTaskPerformer = ({ id, optionType }: TUsersDropdownOption) => {
      const mapPerformer = {
        sourceId: id,
        type: optionType as unknown as ETemplateOwnerType,
      };
      removeTaskPerformer({ taskId: task.id, userId: mapPerformer });
    };

    const onAddTaskPerformer = ({ id, optionType }: TUsersDropdownOption) => {
      const mapPerformer = {
        sourceId: id,
        type: optionType as unknown as ETemplateOwnerType,
      };
      addTaskPerformer({ taskId: task.id, userId: mapPerformer });
    };

    return (
      <>
        {authUser.isAdmin && (
          <UsersDropdown
            isMulti
            controlSize="sm"
            className={styles['responsible']}
            placeholder={formatMessage({ id: 'user.search-field-placeholder' })}
            options={[...performerGroupDropdownOption, ...performerDropdownOption]}
            value={[...performerDropdownValue, ...performerGroupDropdownValue]}
            onChange={onAddTaskPerformer}
            onChangeSelected={onRemoveTaskPerformer}
            onUsersInvited={onUsersInvited}
            onClickInvite={() => trackInviteTeamInPage('Task card')}
            inviteLabel={formatMessage({ id: 'template.invite-team-member' })}
            title={formatMessage({ id: 'task.add-performer' })}
          />
        )}

        {viewMode !== ETaskCardViewMode.Guest && (
          <GuestController ref={guestsControllerRef} taskId={task.id} className={styles['guest-dropdown']} />
        )}
      </>
    );
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setOutputValues((prevOutputFields) => {
      const newFields = getEditedFields(prevOutputFields, apiName, changedProps);

      saveOutputsToStorageDebounced(task.id, newFields);

      return newFields;
    });
  };

  const renderOutputFields = () => {
    if (!isArrayWithItems(outputValues) || status === ETaskStatus.Completed) {
      return null;
    }

    return (
      <div className={styles['task-output']}>
        <p className={styles['task-output__title']}>
          <IntlMessages id="tasks.task-outputs-fill-help" />
        </p>

        {outputValues?.map((field) => (
          <ExtraFieldIntl
            key={field.apiName}
            field={field}
            editField={handleEditField(field.apiName)}
            showDropdown={false}
            mode={EExtraFieldMode.ProcessRun}
            labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
            namePlaceholder={field.name}
            descriptionPlaceholder={field.description}
            wrapperClassName={styles['task-output__field']}
            accountId={accountId}
          />
        ))}
      </div>
    );
  };

  const handleReturnTask = (comment: string) => {
    setTaskReverted({
      taskId: task.id,
      viewMode,
      comment,
    });
    setIsReturnModalOpen(false);
  };

  const renderTaskButtons = () => {
    if (status === ETaskStatus.Completed || task.workflow.status === EWorkflowStatus.Finished) {
      const dateCompleted = task.dateCompleted || task.workflow.dateCompleted;

      const label = dateCompleted ? (
        <>
          {formatMessage({ id: 'task.completed-with-date' })}
          <span className={styles['completed__text-date']}>
            <DateFormat date={dateCompleted} />
          </span>
        </>
      ) : (
        formatMessage({ id: 'task.completed' })
      );

      return (
        <div className={styles['completed']}>
          <DoneInfoIcon />
          <p className={styles['completed__text']}>{label}</p>
        </div>
      );
    }

    const renderCompleteButton = (isDisabled: boolean) => {
      return (
        <Button
          isLoading={status === ETaskStatus.Completing}
          onClick={() =>
            setTaskCompleted({
              taskId,
              viewMode,
              output: outputValues,
            })
          }
          label={formatMessage({ id: 'processes.complete-task' })}
          size="md"
          disabled={isDisabled}
          buttonStyle="yellow"
        />
      );
    };

    const { id: taskId, dateStarted, dateCompleted } = task;
    const isNotFirstTask = workflow?.tasks.find((localTask) => localTask.id === taskId && localTask.number !== 1);
    const isReturnAllowed = viewMode !== ETaskCardViewMode.Guest && isNotFirstTask;
    const isReturnedTask = !dateStarted && !dateCompleted;

    if (isReturnedTask) {
      return (
        <div className={styles['returned']}>
          <ReturnTaskInfoIcon />
          <p className={styles['returned__text']}>{formatMessage({ id: 'task.returned' })}</p>
        </div>
      );
    }

    const isEmbeddedWorkflowsComplete = !task.subWorkflows.some(
      (subWorkflow) => subWorkflow.status !== EWorkflowStatus.Finished,
    );

    return (
      <div className={styles['buttons']}>
        <div className={styles['buttons__complete']}>
          {isEmbeddedWorkflowsComplete ? (
            renderCompleteButton(!isEmbeddedWorkflowsComplete)
          ) : (
            <Tooltip content={formatMessage({ id: 'task.need-complete-embedded-processes' })}>
              <div>{renderCompleteButton(!isEmbeddedWorkflowsComplete)}</div>
            </Tooltip>
          )}
        </div>

        {isReturnAllowed && (
          <Tooltip
            content={
              !isEmbeddedWorkflowsComplete
                ? formatMessage({ id: 'task.need-return-embedded-processes' })
                : formatMessage({ id: 'tasks.task-return-hint' })
            }
          >
            <div>
              <Button
                disabled={!isEmbeddedWorkflowsComplete}
                onClick={() => setIsReturnModalOpen(true)}
                label={isMobile ? undefined : formatMessage({ id: 'processes.return-task' })}
                icon={isMobile ? ReturnToIcon : undefined}
                buttonStyle="transparent-black"
                className={styles['buttons__return']}
                size="md"
                isLoading={status === ETaskStatus.Returning}
              />
            </div>
          </Tooltip>
        )}

        {viewMode !== ETaskCardViewMode.Guest && (
          <Tooltip content={formatMessage({ id: 'task.delegate' })}>
            <Button
              onClick={handleDelegateWorkflow}
              icon={PlayLogoIcon}
              buttonStyle="transparent-black"
              className={styles['buttons__return']}
              size="md"
              isLoading={status === ETaskStatus.Returning}
            />
          </Tooltip>
        )}
      </div>
    );
  };

  const renderWorkflowData = () => {
    if (isWorkflowLoading) {
      return <WorkflowLogSkeleton />;
    }

    return (
      <WorkflowLog
        workflowStatus={workflow?.status || EWorkflowStatus.Running}
        theme="beige"
        isLoading={workflowLog.isLoading}
        items={workflowLog.items}
        sorting={workflowLog.sorting}
        isCommentsShown={workflowLog.isCommentsShown}
        isOnlyAttachmentsShown={workflowLog.isOnlyAttachmentsShown}
        workflowId={workflowLog.workflowId}
        includeHeader
        oldestDeadline={task.dueDate}
        isLogMinimized={false}
        areTasksClickable={viewMode === ETaskCardViewMode.Single}
        minimizedLogMaxEvents={MINIMIZED_LOG_MAX_EVENTS}
        isCommentFieldHidden={viewMode === ETaskCardViewMode.Guest && status === ETaskStatus.Completed}
        isToggleCommentHidden
        sendComment={sendTaskWorkflowLogComments}
        changeWorkflowLogViewSettings={changeTaskWorkflowLogViewSettings}
        onUnmount={() =>
          changeTaskWorkflowLog({
            isOnlyAttachmentsShown: false,
            sorting: EWorkflowsLogSorting.New,
          })
        }
        isInTaskCard
        taskId={task.id}
        taskStatus={task.status}
      />
    );
  };

  return (
    <>
      <ReturnModal
        isOpen={isReturnModalOpen}
        onClose={() => setIsReturnModalOpen(false)}
        onConfirm={handleReturnTask}
      />
      <div
        ref={wrapperRef}
        className={classnames(styles['container'], viewMode === ETaskCardViewMode.Guest && styles['container_guest'])}
      >
        {renderHeader()}
        <p className={styles['description']}>
          <RichText
            text={task.description}
            interactiveChecklists
            renderExtensions={[...createChecklistExtension(task), ...createProgressbarExtension(task)]}
            hideIcon
          />
        </p>
        <div className={styles['info']}>
          <div className={styles['performers']}>
            {renderPerformersControllers()}
            {renderPerformers()}
          </div>

          {viewMode !== ETaskCardViewMode.Guest && (
            <DueIn
              withTime
              timezone={authUser.timezone}
              dateFmt={authUser.dateFmt}
              dueDate={task.dueDate}
              onSave={setDueDate}
              onRemove={deleteDueDate}
              containerClassName={styles['due-in']}
              dateCompleted={task.dateCompleted || task.workflow.dateCompleted}
            />
          )}
        </div>

        <div className={styles['complete-form']}>
          {renderOutputFields()}
          {renderTaskButtons()}
          {viewMode !== ETaskCardViewMode.Guest && !isEmptyArray(task.subWorkflows) && (
            <SubWorkflowsContainer workflows={task.subWorkflows} ancestorTaskId={task.id} />
          )}
        </div>
        {renderWorkflowData()}
      </div>
    </>
  );
}

export type ITaskCardWrapperProps = Omit<ITaskCardProps, 'task'> & {
  task: ITask | null;
};

export function TaskCardWrapper({ task, status, ...restProps }: ITaskCardWrapperProps) {
  if (status === ETaskStatus.Loading) return <TaskCarkSkeleton />;
  if (!task) return null;

  return <TaskCard task={task} status={status} {...restProps} />;
}
