import React, { useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { openTuneViewModal } from '../../../../redux/workflows/slice';
import { EWorkflowsLoadingStatus } from '../../../../types/workflow';
import { EPageTitle } from '../../../../constants/defaultValues';
import { Button, Tooltip } from '../../../UI';
import { TuneViewIcon, DownloadIcon } from '../../../icons';
import { PageTitle } from '../../../PageTitle';
import { getWorkflowTemplatesIdsFilter } from '../../../../redux/selectors/workflows';
import { useWorkflowsExportCsv } from '../../../../hooks/useWorkflowsExportCsv';
import { WorkflowsTableActionsProps } from './types';

import styles from './WorkflowsTable.css';

export function WorkflowsTableActions({
  workflowsLoadingStatus,
  isWideTable = false,
  isMobile,
}: WorkflowsTableActionsProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { handleExportCsvClick, isExporting } = useWorkflowsExportCsv();

  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);

  const isDisabled = useMemo(
    () => templatesIdsFilter.length !== 1 || workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList,
    [templatesIdsFilter.length, workflowsLoadingStatus],
  );

  const isExportDisabled = useMemo(
    () => workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList || isExporting,
    [workflowsLoadingStatus, isExporting],
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
      iconClassName={styles['tune-view-icon']}
      onClick={handleTuneViewClick}
    />
  );

  const exportCsvButton = (
    <Button
      className={styles['tune-view-button']}
      buttonStyle="transparent-black"
      label={
        isMobile
          ? ''
          : formatMessage({ id: isExporting ? 'workflows.export-csv-loading' : 'workflows.export-csv' })
      }
      size="sm"
      disabled={isExportDisabled}
      icon={DownloadIcon}
      onClick={handleExportCsvClick}
    />
  );

  return (
    <div
      className={isWideTable ? styles['container__actions--wide-table'] : styles['container__actions--narrow-table']}
    >
      <PageTitle titleId={EPageTitle.Workflows} className={styles['title']} withUnderline={false} isFromTableView />

      <div className={styles['actions-buttons']}>
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
        {isExportDisabled ? (
          <Tooltip
            content={formatMessage({
              id: isExporting ? 'workflows.export-csv-loading' : 'workflows.export-csv-tooltip',
            })}
            contentClassName={styles['workflow-tune-view-tooltip']}
          >
            <div>{exportCsvButton}</div>
          </Tooltip>
        ) : (
          <Tooltip
            content={formatMessage({ id: 'workflows.export-csv-tooltip-all' })}
            contentClassName={styles['workflow-tune-view-tooltip']}
          >
            <div>{exportCsvButton}</div>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
