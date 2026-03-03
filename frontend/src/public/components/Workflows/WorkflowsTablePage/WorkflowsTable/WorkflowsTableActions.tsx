import React, { useCallback, useMemo, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { openTuneViewModal } from '../../../../redux/workflows/slice';
import { EWorkflowsLoadingStatus } from '../../../../types/workflow';
import { EPageTitle } from '../../../../constants/defaultValues';
import { Button, Tooltip } from '../../../UI';
import { TuneViewIcon, DownloadIcon } from '../../../icons';
import { PageTitle } from '../../../PageTitle';
import {
  getWorkflowTemplatesIdsFilter,
  getSavedFields,
  getWorkflowsSorting,
  getWorkflowsStatus,
  getWorkflowStartersIdsFilter,
  getWorkflowTasksApiNamesFilter,
  getWorkflowPerformersIdsFilter,
  getWorkflowPerformersGroupsIdsFilter,
  getWorkflowsSearchText,
} from '../../../../redux/selectors/workflows';
import { getAccountsUsers } from '../../../../redux/selectors/accounts';
import { getGroups } from '../../../../redux/selectors/groups';
import { getTimezone } from '../../../../redux/selectors/authUser';
import { buildWorkflowsCsvContent, downloadWorkflowsCsv } from '../../../../utils/workflows/exportWorkflowsToCsv';
import { fetchAllWorkflowsForExport } from '../../../../api/workflows/fetchAllWorkflowsForExport';
import { NotificationManager } from '../../../UI/Notifications';
import { DEFAULT_HEADER_KEYS } from './constants';
import { WorkflowsTableActionsProps } from './types';

import styles from './WorkflowsTable.css';

export function WorkflowsTableActions({
  workflowsLoadingStatus,
  isWideTable = false,
  isMobile,
}: WorkflowsTableActionsProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);
  const selectedFields = useSelector(getSavedFields);
  const sorting = useSelector(getWorkflowsSorting);
  const statusFilter = useSelector(getWorkflowsStatus);
  const workflowStartersIdsFilter = useSelector(getWorkflowStartersIdsFilter);
  const tasksApiNamesFilter = useSelector(getWorkflowTasksApiNamesFilter);
  const performersIdsFilter = useSelector(getWorkflowPerformersIdsFilter);
  const performersGroupIdsFilter = useSelector(getWorkflowPerformersGroupsIdsFilter);
  const searchText = useSelector(getWorkflowsSearchText);
  const users = useSelector(getAccountsUsers);
  const groups = useSelector(getGroups);
  const timezone = useSelector(getTimezone);

  const [isExporting, setIsExporting] = useState(false);

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

  const handleExportCsvClick = useCallback(() => {
    setIsExporting(true);
    const fields = selectedFields.length ? selectedFields : DEFAULT_HEADER_KEYS;
    fetchAllWorkflowsForExport({
      statusFilter,
      sorting,
      templatesIdsFilter,
      tasksApiNamesFilter,
      performersIdsFilter,
      performersGroupIdsFilter,
      workflowStartersIdsFilter,
      searchText,
      fields,
    })
      .then((items) => {
        if (items.length === 0) {
          NotificationManager.warning({
            title: formatMessage({ id: 'workflows.export-csv-empty-title' }),
            message: formatMessage({ id: 'workflows.export-csv-empty-message' }),
          });
          return;
        }
        const optionalFieldsFromWorkflow = items[0]?.fields ?? [];
        const headerLabels: Record<string, string> = {
          'system-column-workflow': formatMessage({ id: 'workflows.name' }),
          'system-column-templateName': formatMessage({ id: 'workflows.filter-column-template-name' }),
          'system-column-starter': formatMessage({ id: 'workflows.filter-column-starter' }),
          'system-column-progress': formatMessage({ id: 'workflows.filter-column-progress' }),
          'system-column-step': formatMessage({ id: 'workflows.filter-column-tasks' }),
          'system-column-performer': formatMessage({ id: 'workflows.filter-column-performers' }),
        };
        optionalFieldsFromWorkflow.forEach((field) => {
          headerLabels[field.apiName] = field.name;
        });
        const csvContent = buildWorkflowsCsvContent({
          workflows: items,
          users,
          groups,
          selectedFields: fields,
          optionalFieldsFromWorkflow,
          timezone: timezone ?? undefined,
          headerLabels,
          deletedGroupFallbackTemplate: formatMessage(
            { id: 'workflows.export-deleted-group' },
            { id: '{id}' },
          ),
        });
        downloadWorkflowsCsv(csvContent);
      })
      .catch(() => {
        NotificationManager.notifyApiError(null, { message: 'workflows.export-csv-fail' });
      })
      .finally(() => {
        setIsExporting(false);
      });
  }, [
    formatMessage,
    selectedFields,
    statusFilter,
    sorting,
    templatesIdsFilter,
    tasksApiNamesFilter,
    performersIdsFilter,
    performersGroupIdsFilter,
    workflowStartersIdsFilter,
    searchText,
    users,
    groups,
    timezone,
  ]);

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
