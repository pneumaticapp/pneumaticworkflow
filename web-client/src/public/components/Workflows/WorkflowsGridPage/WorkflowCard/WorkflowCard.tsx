/* eslint-disable */
import * as React from 'react';
import * as classnames from 'classnames';
import { IntlShape } from 'react-intl';

import { EWorkflowStatus, IWorkflow } from '../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../utils/dateTime';
import { isArrayWithItems } from '../../../../utils/helpers';
import { WorkflowCardUsers } from '../../../WorkflowCardUsers';
import { ProgressBar } from '../../../ProgressBar';
import { sanitizeText } from '../../../../utils/strings';
import { DateFormat } from '../../../UI/DateFormat';
import { TemplateName } from '../../../UI/TemplateName';
import { getWorkflowProgressColor } from '../../utils/getWorkflowProgressColor';
import { getWorkflowProgress } from '../../utils/getWorkflowProgress';
import { WorkflowControlls } from '../../WorkflowControlls';
import { Dropdown } from '../../../UI';
import { MoreIcon } from '../../../icons';
import { ProgressbarTooltipContents } from '../../utils/ProgressbarTooltipContents';

import styles from '../WorkflowsGridPage.css';

export interface IWorkflowCardProps {
  intl: IntlShape;
  workflow: IWorkflow;
  onCardClick(e: React.MouseEvent): void;
  onWorkflowEnded?(): void;
  onWorkflowSnoozed?(): void;
  onWorkflowDeleted?(): void;
  onWorkflowResumed?(): void;
}

export interface IWorkflowCardState {
  isCardPending: boolean;
}

export class WorkflowCard extends React.PureComponent<IWorkflowCardProps> {
  public state = {
    isCardPending: false,
  };

  public render() {
    const {
      intl: { formatMessage },
      onCardClick,
      onWorkflowEnded,
      onWorkflowSnoozed,
      onWorkflowDeleted,
      onWorkflowResumed,
      workflow,
      workflow: {
        name: workflowName,
        tasksCount,
        currentTask,
        status,
        template,
        isLegacyTemplate,
        legacyTemplateName,
        task: { delay, name: taskName, performers: selectedUsers, dueDate: taskDueDate },
        isUrgent,
        dueDate,
      },
    } = this.props;

    const { isCardPending } = this.state;

    const progress = getWorkflowProgress({ currentTask, tasksCount, status });

    const getSnoozedText = () => {
      if (!delay) {
        return '';
      }

      return formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(delay) });
    };

    const renderCardFooter = () => {
      if (status !== EWorkflowStatus.Running) {
        return null;
      }

      return (
        <div className={styles['footer-users-and-links']}>
          <WorkflowCardUsers users={selectedUsers} />
        </div>
      );
    };

    const renderCardSubtitle = () => {
      const {
        intl: { formatMessage },
        workflow: { statusUpdated },
      } = this.props;

      const subtitlesMap = {
        [EWorkflowStatus.Running]: taskName,
        [EWorkflowStatus.Snoozed]: getSnoozedText(),
        [EWorkflowStatus.Finished]: formatMessage(
          { id: 'workflows.finished' },
          { date: <DateFormat date={statusUpdated} /> },
        ),
        [EWorkflowStatus.Aborted]: '',
      };

      return <div className={classnames(styles['card-task'], 'truncate')}>{subtitlesMap[status]}</div>;
    };

    return (
      <>
        <div className={styles['card-wrapper']}>
          <div
            role="button"
            className={classnames(
              styles['card'],
              isUrgent && styles['card-urgent'],
              isCardPending && styles['card-pending'],
            )}
            onClick={onCardClick}
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
            <div className={styles['card-footer']}>
              <ProgressBar
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
      </>
    );
  }
}
