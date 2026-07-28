import * as React from 'react';
import { useIntl } from 'react-intl';

import { Avatar, TAvatarUser } from '../../../../UI/Avatar';
import { DoneInfoIcon } from '../../../../icons';
import { DateFormat } from '../../../../UI/DateFormat';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../../../../KickoffOutputs';
import { isArrayWithItems } from '../../../../../utils/helpers';
import { EWorkflowLogEvent, IWorkflowLogItem, IWorkflowLogTask } from '../../../../../types/workflow';

import styles from './WorkflowLogAiAgent.css';

export type TWorkflowLogAiAgentProps = Pick<IWorkflowLogItem, 'text' | 'created' | 'type'>;

export interface IWorkflowLogAiAgentProps extends TWorkflowLogAiAgentProps {
  currentTask: IWorkflowLogTask | null;
  isOnlyAttachmentsShown?: boolean;
}

export function WorkflowLogAiAgent({
  text,
  created,
  type,
  currentTask,
  isOnlyAttachmentsShown = false,
}: IWorkflowLogAiAgentProps) {
  const { formatMessage } = useIntl();

  const isCompleted = type === EWorkflowLogEvent.AiAgentCompleted;
  const agentAvatar = { type: 'ai_agent', firstName: text || '' } as unknown as TAvatarUser;

  const renderOutputValues = () => {
    if (!isCompleted) {
      return null;
    }
    const hasOutputValue =
      isArrayWithItems(currentTask?.output.filter(Boolean)) || isArrayWithItems(currentTask?.fieldsets);

    if (!hasOutputValue) {
      return null;
    }

    return (
      <KickoffOutputs
        containerClassName={styles['outputs-container']}
        viewMode={EKickoffOutputsViewModes.Short}
        outputs={currentTask?.output.filter(Boolean)}
        fieldsets={currentTask?.fieldsets || []}
        isOnlyAttachmentsShown={isOnlyAttachmentsShown}
      />
    );
  };

  return (
    <div className={styles['container']}>
      <div className={styles['avatar']}>
        <Avatar user={agentAvatar} size="lg" sizeMobile="sm" />
      </div>
      <div className={styles['body']}>
        <p className={styles['title']}>
          <span className={styles['title__text']}>
            {isCompleted ? text : formatMessage({ id: 'workflows.log-ai-left-title' })}
          </span>
          {isCompleted && (
            <span className={styles['title__icon']}>
              <DoneInfoIcon />
            </span>
          )}
          <span className={styles['title__date']}>
            <DateFormat date={created} />
          </span>
        </p>
        {!isOnlyAttachmentsShown && (
          <div className={styles['text']}>
            {isCompleted
              ? formatMessage({ id: 'workflows.log-complete' }, { taskName: currentTask?.name })
              : text}
          </div>
        )}
        {renderOutputValues()}
      </div>
    </div>
  );
}
