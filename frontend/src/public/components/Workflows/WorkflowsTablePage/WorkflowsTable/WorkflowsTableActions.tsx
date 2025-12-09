import React, { useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { IApplicationState } from '../../../../types/redux';
import { openTuneViewModal } from '../../../../redux/workflows/slice';
import { EWorkflowsLoadingStatus } from '../../../../types/workflow';
import { EPageTitle } from '../../../../constants/defaultValues';
import { Button, Tooltip } from '../../../UI';
import { TuneViewIcon } from '../../../icons';
import { PageTitle } from '../../../PageTitle';

import styles from './WorkflowsTable.css';

interface WorkflowsTableActionsProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  isWideTable?: boolean;
  isMobile?: boolean;
}

export function WorkflowsTableActions({
  workflowsLoadingStatus,
  isWideTable = false,
  isMobile,
}: WorkflowsTableActionsProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const templatesIdsFilter = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.values.templatesIdsFilter,
  );
  const isDisabled = useMemo(
    () => templatesIdsFilter.length !== 1 || workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList,
    [templatesIdsFilter.length, workflowsLoadingStatus],
  );

  const handleTuneViewClick = () => {
    dispatch(openTuneViewModal());
  };

  const tuneViewButton = (
    <Button
      className={styles['tune-view-button']}
      buttonStyle="transparent-black"
      label={isMobile ? '' : formatMessage({ id: 'workflow.tune-view-button' })}
      size="sm"
      disabled={isDisabled}
      icon={TuneViewIcon}
      onClick={handleTuneViewClick}
    />
  );

  return (
    <div
      className={isWideTable ? styles['container__actions--wide-table'] : styles['container__actions--narrow-table']}
    >
      <PageTitle titleId={EPageTitle.Workflows} className={styles['title']} withUnderline={false} isFromTableView />

      {isDisabled ? (
        <Tooltip
          content={formatMessage({ id: 'workflow.tune-view-tooltip' })}
          appendTo={() => document.body}
          contentClassName={styles['workflow-tune-view-tooltip']}
        >
          <div>{tuneViewButton}</div>
        </Tooltip>
      ) : (
        tuneViewButton
      )}
    </div>
  );
}
