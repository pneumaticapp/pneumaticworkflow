import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';

import { Avatar } from '../UI/Avatar';
import { EWorkflowLogEvent } from '../../types/workflow';
import { FeedItemIcon } from './FeedItemIcon';
import { getUserFullName, EXTERNAL_USER } from '../../utils/users';
import { IHighlightsItem } from '../../types/highlights';
import { TUserListItem } from '../../types/user';
import { EditIcon, MoreIcon } from '../icons';
import { UserData } from '../UserData';
import { ERoutes } from '../../constants/routes';
import { Dropdown, Loader, TDropdownOption } from '../UI';

import { FeedItemHeader } from './FeedItemHeader';
import { DateFormat } from '../UI/DateFormat';

import styles from './FeedItem.css';

export interface IFeedItem extends IHighlightsItem {
  applyUserFilter(userId?: number): () => void;
  applyTemplatesFilter(tepmlateId?: number): () => void;
  isProcessLogPopupLoading?: boolean;
  item: IHighlightsItem;
  openProcessLogPopup(): void;
  redirectToTemplate(templateId?: number): () => void;
}

export function FeedItem({
  applyUserFilter,
  applyTemplatesFilter,
  isProcessLogPopupLoading,
  item,
  openProcessLogPopup,
  redirectToTemplate,
}: IFeedItem) {
  const { formatMessage } = useIntl();

  const {
    created,
    task,
    text,
    type,
    userId,
    workflow: { template, name: workflowName, isExternal, id: workflowId },
  } = item;

  const isEventAllowed = ALLOWED_EVENT_TYPES.includes(type);
  const isAiAgentEvent = type === EWorkflowLogEvent.AiAgentCompleted || type === EWorkflowLogEvent.AiAgentLeft;

  if (!isEventAllowed) {
    return null;
  }

  const renderItem = (user: TUserListItem) => {
    const userName = getUserFullName(isExternal ? EXTERNAL_USER : user);
    const dropdownOptions: TDropdownOption[] = [
      ...(template
        ? [
                {
                  label: formatMessage({ id: 'process-highlights.dropdown-edit-template' }),
                  onClick: redirectToTemplate(template.id),
                  Icon: EditIcon,
                  size: 'lg',
                } as TDropdownOption,
        ]
        : []),
      ...(template
        ? [
                {
                  label: formatMessage({ id: 'process-highlights.review-workflow' }, { workflow: template.name }),
                  onClick: applyTemplatesFilter(template.id),
                  size: 'lg',
                } as TDropdownOption,
        ]
        : []),
      ...(!isAiAgentEvent
        ? [
                {
                  label: formatMessage({ id: 'process-highlights.review-workflows-of' }, { user: userName }),
                  onClick: applyUserFilter(user.id),
                  size: 'lg',
                } as TDropdownOption,
        ]
        : []),
    ];

    return (
          <div className={styles['feed-item__container']}>
            {isProcessLogPopupLoading && <Loader />}
            <div className={styles['feed-item__header']}>
              <Avatar user={user} size="sm" containerClassName={styles['header__avatar']} />
              <span className={styles['performer__name']}>{userName}</span>
              <div className={styles['feed-item__icon']}>
                <FeedItemIcon type={type} task={task} />
              </div>

              <Link
                className={styles['performer__datetime']}
                to={task ? `${ERoutes.Tasks}${task?.id}` : `${ERoutes.Workflows}${workflowId}`}
              >
                <DateFormat date={created} />
              </Link>

              <div className={styles['card-more-container']}>
                <Dropdown
                  renderToggle={(isOpen) => (
                    <MoreIcon className={classnames(styles['card-more'], isOpen && styles['card-more_active'])} />
                  )}
                  options={dropdownOptions}
                />
              </div>
            </div>
            <div className={styles['feed-item__header-container']}>
              <FeedItemHeader {...item} />
            </div>
            <div
              className={styles['feed-item__body']}
              onClick={openProcessLogPopup}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  openProcessLogPopup();
                }
              }}
              role="button"
              tabIndex={0}
            >
              <div className={styles['feed-item__content']}>
                <span className={styles['body__process-name']}>{workflowName}</span>
                <div className={styles['info__task']}>
                  <span className={styles['task__name']}>
                    {type === EWorkflowLogEvent.WorkflowsReturned
                      ? formatMessage({ id: 'task.log-returned' }, { taskName: task?.name })
                      : task?.name}
                  </span>
                </div>
              </div>
            </div>
          </div>
    );
  };

  if (isAiAgentEvent) {
    // AI events carry no user id; the agent name travels in the event
    // text ("Agent" for completions, "Agent: reason" for left events)
    const agentName = (type === EWorkflowLogEvent.AiAgentLeft ? text.split(':')[0] : text) || 'AI agent';
    const aiAgentUser = {
      id: 0,
      type: 'ai_agent',
      firstName: agentName,
      lastName: '',
      photo: '',
    } as unknown as TUserListItem;
    return renderItem(aiAgentUser);
  }

  return <UserData userId={userId}>{(user) => (user ? renderItem(user) : null)}</UserData>;
}

export const ALLOWED_EVENT_TYPES = [
  EWorkflowLogEvent.TaskComplete,
  EWorkflowLogEvent.TaskComment,
  EWorkflowLogEvent.WorkflowRun,
  EWorkflowLogEvent.WorkflowFinished,
  EWorkflowLogEvent.WorkflowComplete,
  EWorkflowLogEvent.WorkflowsReturned,
  EWorkflowLogEvent.TaskRevert,
  EWorkflowLogEvent.WorkflowIsUrgent,
  EWorkflowLogEvent.WorkflowIsNotUrgent,
  EWorkflowLogEvent.AddedPerformer,
  EWorkflowLogEvent.RemovedPerformer,
  EWorkflowLogEvent.AddedPerformerGroup,
  EWorkflowLogEvent.RemovedPerformerGroup,
  EWorkflowLogEvent.WorkflowSnoozedManually,
  EWorkflowLogEvent.WorkflowResumed,
  EWorkflowLogEvent.DueDateChanged,
  EWorkflowLogEvent.AiAgentCompleted,
  EWorkflowLogEvent.AiAgentLeft,
];
