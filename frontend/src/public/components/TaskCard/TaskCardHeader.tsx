import React, { MouseEvent, useRef } from 'react';
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';

import { sanitizeText } from '../../utils/strings';
import { getTaskDetailRoute, getWorkflowDetailedRoute, isTaskDetailRoute } from '../../utils/routes';
import { history } from '../../utils/history';
import { Header } from '../UI/Typeography/Header';
import { Tooltip } from '../UI';
import { DateFormat } from '../UI/DateFormat';
import { ETaskCardViewMode, TTaskCardHeaderProps } from './types';

import styles from './TaskCard.css';

export function TaskCardHeader({ task, viewMode, workflowLog, openWorkflowLogPopup }: TTaskCardHeaderProps) {
  const { formatMessage } = useIntl();
  const workflowLinkRef = useRef(null);
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
  const handleOpenWorkflowPopup = (workflowId: number | null) => (event: MouseEvent) => {
    event.preventDefault();
    if (workflowId) {
      openWorkflowLogPopup({ workflowId });
    }
  };

  if (viewMode === ETaskCardViewMode.Guest) {
    return (
      <Header size="4" tag="h1" className={styles['guest-task-name']}>
        {name}
      </Header>
    );
  }

  return (
    <>
      <div className={styles.pretitle}>
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
      <span className={styles.date}>
        <DateFormat date={dateStarted} />
      </span>
    </>
  );
}
