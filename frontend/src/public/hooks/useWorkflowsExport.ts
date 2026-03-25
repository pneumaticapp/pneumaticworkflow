import { useCallback, useState } from 'react';
import { useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { ITableViewFields } from '../types/template';
import { fetchAllWorkflowsForExport } from '../api/workflows/fetchAllWorkflowsForExport';
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
} from '../redux/selectors/workflows';
import { getAccountsUsers } from '../redux/selectors/accounts';
import { getGroupsList } from '../redux/selectors/groups';
import { getTimezone } from '../redux/selectors/authUser';
import {
  buildWorkflowsExportRows,
  buildWorkflowsXlsxBuffer,
  downloadWorkflowsExcel,
} from '../utils/workflows/exportWorkflowsToExcel';
import { NotificationManager } from '../components/UI/Notifications';
import { ALL_SYSTEM_FIELD_NAMES } from '../components/Workflows/WorkflowsTablePage/WorkflowsTable/constants';

type TFormatMessage = (params: { id: string }, values?: Record<string, string>) => string;

function getExportHeaderLabels(
  formatMessage: TFormatMessage,
  optionalFieldsFromWorkflow: ITableViewFields[],
): Record<string, string> {
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
  return headerLabels;
}

export function useWorkflowsExport() {
  const { formatMessage } = useIntl();
  const [isExporting, setIsExporting] = useState(false);

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
  const groups = useSelector(getGroupsList);
  const timezone = useSelector(getTimezone);

  const handleExportClick = useCallback(async () => {
    setIsExporting(true);
    try {
      const fields = selectedFields.length ? selectedFields : ALL_SYSTEM_FIELD_NAMES;
      const items = await fetchAllWorkflowsForExport({
        statusFilter,
        sorting,
        templatesIdsFilter,
        tasksApiNamesFilter,
        performersIdsFilter,
        performersGroupIdsFilter,
        workflowStartersIdsFilter,
        searchText,
        fields,
      });

      if (items.length === 0) {
        NotificationManager.warning({
          title: formatMessage({ id: 'workflows.export-excel-empty-title' }),
          message: formatMessage({ id: 'workflows.export-excel-empty-message' }),
        });
        return;
      }

      const optionalFieldsFromWorkflow = items[0]?.fields ?? [];
      const headerLabels = getExportHeaderLabels(formatMessage, optionalFieldsFromWorkflow);
      const rows = buildWorkflowsExportRows({
        workflows: items,
        users,
        groups,
        selectedFields: fields,
        optionalFieldsFromWorkflow,
        timezone: timezone ?? undefined,
        headerLabels,
        multipleTasksLabel: formatMessage({ id: 'workflows.multiple-active-tasks' }),
        deletedGroupFallbackTemplate: formatMessage(
          { id: 'workflows.export-deleted-group' },
          { id: '{id}' },
        ),
      });
      const buffer = await buildWorkflowsXlsxBuffer(rows);
      downloadWorkflowsExcel(buffer);
    } catch (error) {
      NotificationManager.notifyApiError(error, { message: 'workflows.export-excel-fail' });
    } finally {
      setIsExporting(false);
    }
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

  return { handleExportClick, isExporting };
}
