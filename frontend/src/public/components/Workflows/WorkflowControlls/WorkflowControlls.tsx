import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import Switch from 'rc-switch';
import classnames from 'classnames';

import { TDropdownOption } from '../../UI';
import {
  UnionIcon,
  PencilIcon,
  FlagIcon,
  UnsnoozeIcon,
  TrashIcon,
  AlarmIcon,
  UrgentIcon,
  ReturnToIcon,
} from '../../icons';
import { isArrayWithItems } from '../../../utils/helpers';
import { getAuthUser } from '../../../redux/selectors/user';
import { EWorkflowStatus, IPassedTask, IWorkflowClient, IWorkflowDetailsClient } from '../../../types/workflow';
import { NotificationManager } from '../../UI/Notifications';
import {
  setWorkflowFinished,
  setWorkflowResumed,
  deleteWorkflowAction,
  returnWorkflowToTaskAction,
  cloneWorkflowAction,
  editWorkflow,
  snoozeWorkflow,
} from '../../../redux/actions';
import { getSnoozeOptions } from '../utils/getSnoozeOptions';
import { getTemplateEditRoute } from '../../../utils/routes';
import { history } from '../../../utils/history';

import { checkCanControlWorkflow } from './utils/checkCanControlWorkflow';

import styles from './WorkflowControlls.css';

export interface IWorkflowControllsProps {
  workflow: IWorkflowClient | IWorkflowDetailsClient;
  timezone: string;
  onWorkflowDeleted?(): void;
  onWorkflowEnded?(): void;
  onWorkflowSnoozed?(workflow: IWorkflowClient): void;
  onWorkflowResumed?(): void;
  onWorkflowReturn?(): void;
  onChangeUrgent?(isChecked: boolean): void;
  children(options: TDropdownOption[]): React.ReactNode;
}

export function WorkflowControllsComponents({
  workflow,
  timezone,
  onWorkflowDeleted,
  onWorkflowEnded,
  onWorkflowSnoozed,
  onWorkflowResumed,
  onWorkflowReturn,
  onChangeUrgent,
  children,
}: IWorkflowControllsProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const [isUrgent, setIsUrgent] = React.useState(workflow.isUrgent);

  const { authUser } = useSelector(getAuthUser);
  const canControlWorkflow = checkCanControlWorkflow(authUser, workflow.owners);

  if (!canControlWorkflow) {
    return <>{children([])}</>;
  }

  const workflowId = workflow.id;
  const templateId = workflow.template?.id;
  const completedTasks = workflow?.completedTasks;
  const snoozeOptions = getSnoozeOptions(formatMessage, timezone);

  const canCloneWorkflow = Boolean(workflow.template?.isActive);
  const canEndWorkflow = workflow.finalizable && workflow.status !== EWorkflowStatus.Finished;
  const canSnoozeWorkflow = workflow.status === EWorkflowStatus.Running;
  const canResumeWorkflow = workflow.status === EWorkflowStatus.Snoozed;

  const handleOnClone = () => {
    if (!workflow.template) {
      NotificationManager.error({
        title: 'workflows.no-template-access',
      });

      return;
    }

    dispatch(
      cloneWorkflowAction({
        workflowId,
        workflowName: workflow.name,
        templateId,
      }),
    );
  };

  const handleResumeWorkflow = () => {
    if (workflowId) {
      dispatch(
        setWorkflowResumed({
          workflowId,
          onSuccess: onWorkflowResumed,
        }),
      );
    }
  };

  const handleEndWorkflow = () => {
    if (workflowId) {
      dispatch(
        setWorkflowFinished({
          workflowId,
          onWorkflowEnded,
        }),
      );
    }
  };

  const handleDeleteWorkflow = () => {
    dispatch(deleteWorkflowAction({ workflowId, onSuccess: onWorkflowDeleted }));
  };

  const handleChangeUrgent = (isChecked: boolean) => {
    onChangeUrgent?.(isChecked);
    setIsUrgent(isChecked);
    dispatch(
      editWorkflow({
        typeChange: 'control',
        isUrgent: isChecked,
        workflowId,
      }),
    );
  };

  const handleOnReturn = (task: IPassedTask) => () => {
    dispatch(returnWorkflowToTaskAction({ workflowId, taskId: task.id, onSuccess: onWorkflowReturn }));
  };

  const handleEditTemplate = () => {
    if (templateId) {
      history.push(getTemplateEditRoute(templateId));
    }
  };

  const handleSnoozeWorkflow = (date: string) => {
    dispatch(
      snoozeWorkflow({
        workflowId,
        date,
        onSuccess: onWorkflowSnoozed,
      }),
    );
  };

  const options: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'workflows.card-resume' }),
      onClick: handleResumeWorkflow,
      Icon: UnsnoozeIcon,
      withConfirmation: true,
      isHidden: !canResumeWorkflow,
      color: 'green',
      size: 'sm',
    },
    {
      mapKey: 'workflows.card-urgent',
      label: (
        <div className={styles['urgent-wrapper']}>
          <span className={styles['urgent-text']}>{formatMessage({ id: 'workflows.card-urgent' })}</span>
          <Switch
            className={classnames('custom-switch custom-switch-primary custom-switch-small ml-auto')}
            checked={isUrgent}
            onChange={handleChangeUrgent}
            checkedChildren={null}
            unCheckedChildren={null}
          />
        </div>
      ),
      Icon: UrgentIcon,
      isHidden: workflow.status === EWorkflowStatus.Finished,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.card-return' }),
      isHidden: !isArrayWithItems(completedTasks),
      Icon: ReturnToIcon,
      subOptions: [...completedTasks].reverse().map((item, index) => {
        const taskIndex = String(completedTasks.length - index).padStart(2, '0');

        return {
          mapKey: `return-task-${item.name}-${taskIndex}`,
          label: (
            <div className={styles['task-item']}>
              <div className={styles['task-item__text']}>{item.name}</div>
              <div className={styles['task-item__index']}>{taskIndex}</div>
            </div>
          ),
          onClick: handleOnReturn(item),
          withConfirmation: true,
          size: 'lg',
        };
      }),
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.card-snooze' }),
      Icon: AlarmIcon,
      isHidden: !canSnoozeWorkflow,
      subOptions: snoozeOptions.map((option) => {
        return {
          mapKey: `snooze-${option.title}-${option.dateISOString}`,
          label: (
            <>
              <span className={styles['dropdown-title']}>{option.title}</span>
              <span className={styles['dropdown-subtitle']}>{option.dateString}</span>
            </>
          ),
          onClick: () => handleSnoozeWorkflow(option.dateISOString),
          size: 'lg',
        };
      }),
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.clone' }),
      onClick: handleOnClone,
      Icon: UnionIcon,
      isHidden: !canCloneWorkflow,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.edit-template' }),
      onClick: handleEditTemplate,
      Icon: PencilIcon,
      isHidden: !templateId,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.card-end-workflow' }),
      onClick: handleEndWorkflow,
      Icon: FlagIcon,
      withConfirmation: true,
      isHidden: !canEndWorkflow,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.card-delete' }),
      onClick: handleDeleteWorkflow,
      Icon: TrashIcon,
      withConfirmation: true,
      isHidden: workflow.status === EWorkflowStatus.Aborted,
      withUpperline: true,
      color: 'red',
      size: 'sm',
    },
  ];

  return <>{children(options)}</>;
}
