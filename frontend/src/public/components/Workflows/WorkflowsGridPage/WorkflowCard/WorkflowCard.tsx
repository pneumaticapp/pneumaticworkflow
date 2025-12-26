import React from 'react';
import classnames from 'classnames';
import { IntlShape } from 'react-intl';

import { EWorkflowStatus, IWorkflowClient } from '../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../utils/dateTime';
import { isArrayWithItems } from '../../../../utils/helpers';
import { WorkflowCardUsers } from '../../../WorkflowCardUsers';
import { ProgressBar } from '../../../ProgressBar';
import { sanitizeText } from '../../../../utils/strings';
import { DateFormat } from '../../../UI/DateFormat';
import { TemplateName } from '../../../UI/TemplateName';
import { WorkflowControlls } from '../../WorkflowControlls';
import { Dropdown, Tooltip } from '../../../UI';
import { MoreIcon } from '../../../icons';

import styles from '../WorkflowsGridPage.css';
import { TaskNamesTooltipContent } from '../../utils/TaskNamesTooltipContent';

export interface IWorkflowCardProps {
  intl: IntlShape;
  workflow: IWorkflowClient;
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
  const isCardPending = false;
  const {
    name: workflowName,
    status,
    template,
    isLegacyTemplate,
    legacyTemplateName,
    isUrgent,
    tasks,
    oneActiveTaskName,
    dateCompleted,
    minDelay,
    areOverdueTasks,
    areMultipleTasks,
    selectedUsers,
    multipleTasksNamesByApiNames,
  } = workflow;

  const namesTooltip = areMultipleTasks && TaskNamesTooltipContent(multipleTasksNamesByApiNames);

  const getSnoozedText = () => {
    if (!minDelay) return '';

    return formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(minDelay) });
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
          <div className={styles['card-multiple-tasks-title']}>
            {formatMessage({ id: 'workflows.multiple-active-tasks' })}
          </div>
        </Tooltip>
      ) : (
        oneActiveTaskName
      ),
      [EWorkflowStatus.Snoozed]: getSnoozedText(),
      [EWorkflowStatus.Finished]:
        dateCompleted && formatMessage({ id: 'workflows.finished' }, { date: <DateFormat date={dateCompleted} /> }),
      [EWorkflowStatus.Aborted]: '',
    };

    const extraTextStyle =
      status === EWorkflowStatus.Snoozed || status === EWorkflowStatus.Finished ? styles['card-extra-text'] : '';
    return <div className={classnames(styles['card-task'], 'truncate', extraTextStyle)}>{subtitlesMap[status]}</div>;
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
          <ProgressBar tasks={tasks} background="white" containerClassName={styles['progress-bar-container']} />
          {renderCardSubtitle()}
          {renderCardFooter()}
        </div>
      </div>
    </div>
  );
};
