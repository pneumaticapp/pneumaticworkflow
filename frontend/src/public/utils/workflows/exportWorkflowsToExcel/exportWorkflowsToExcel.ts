import { ITableViewFields, EExtraFieldType, ETemplateOwnerType } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { IGroup } from '../../../redux/team/types';
import { getUserFullName, EXTERNAL_USER } from '../../users';
import { getUserById } from '../../../components/UserData/utils/getUserById';
import { toDateString } from '../../dateTime';
import { getWorkflowProgress } from '../../../components/Workflows/utils/getWorkflowProgress';
import { ALL_SYSTEM_FIELD_NAMES } from '../../../components/Workflows/WorkflowsTablePage/WorkflowsTable/constants';
import { IExportWorkflowsToExcelConfig } from './types';

export const WORKFLOWS_XLSX_MIME =
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

export const WORKFLOWS_XLSX_DEFAULT_FILENAME = 'workflows.xlsx';


function getStarterDisplayName(
  workflowStarter: number | null,
  isExternal: boolean,
  users: TUserListItem[],
): string {
  if (workflowStarter === null) return '';
  if (isExternal) return getUserFullName(EXTERNAL_USER);
  const user = getUserById(users, workflowStarter);
  return user ? getUserFullName(user) : '';
}

function getPerformersDisplayName(
  selectedUsers: { type: ETemplateOwnerType; sourceId: number }[],
  users: TUserListItem[],
  groups: IGroup[],
  deletedGroupFallbackTemplate: string,
): string {
  if (!selectedUsers?.length) return '';
  return selectedUsers
    .map((p) => {
      if (p.type === ETemplateOwnerType.UserGroup) {
        const group = groups.find((g) => g.id === p.sourceId);
        return group?.name ?? deletedGroupFallbackTemplate.replace(/\{id\}/g, String(p.sourceId));
      }
      const user = getUserById(users, p.sourceId);
      return user ? getUserFullName(user) : '';
    })
    .filter(Boolean)
    .join(', ');
}

function getOptionalFieldValue(
  field: ITableViewFields | undefined,
  timezone?: string,
  users?: TUserListItem[],
  groups?: IGroup[],
): string {
  if (!field) return '';
  switch (field.type) {
    case EExtraFieldType.Text:
      return field.clearValue ?? String(field.value ?? '');
    case EExtraFieldType.Date:
      return field.value ? (toDateString(field.value as string, timezone) ?? '') : '';
    case EExtraFieldType.User:
      if (field.groupId && groups?.length) {
        const group = groups.find((g) => g.id === field.groupId);
        return group?.name ?? '';
      }
      if (field.userId && users?.length) {
        const user = getUserById(users, field.userId);
        return user ? getUserFullName(user) : '';
      }
      return '';
    case EExtraFieldType.Url:
    case EExtraFieldType.Number:
    case EExtraFieldType.String:
    case EExtraFieldType.Checkbox:
    case EExtraFieldType.Radio:
      return String(field.value ?? '');
    case EExtraFieldType.File:
      return field.clearValue ?? (field.markdownValue ? '—' : '');
    default:
      return field.clearValue ?? String(field.value ?? '');
  }
}

export function buildWorkflowsExportRows({
  workflows,
  users,
  groups,
  selectedFields,
  optionalFieldsFromWorkflow,
  timezone,
  headerLabels,
  multipleTasksLabel,
  deletedGroupFallbackTemplate,
}: IExportWorkflowsToExcelConfig): string[][] {
  const headerKeys = selectedFields.length > 0
    ? selectedFields
    : [
      ...ALL_SYSTEM_FIELD_NAMES,
      ...(optionalFieldsFromWorkflow ?? []).map((f) => f.apiName),
    ];

  const headerRow = headerKeys.map((key) => headerLabels[key] ?? key);
  const bodyRows: string[][] = [];

  workflows.forEach((workflow) => {
    const progress = getWorkflowProgress({
      completedTasks: workflow.completedTasks,
      tasksCountWithoutSkipped: workflow.tasksCountWithoutSkipped,
    });
    const stepLabel = workflow.areMultipleTasks
      ? multipleTasksLabel
      : (workflow.oneActiveTaskName ?? '');

    const systemValues: Record<string, string> = {
      'system-column-workflow': workflow.name,
      'system-column-templateName': workflow.template?.name ?? '',
      'system-column-starter': getStarterDisplayName(
        workflow.workflowStarter,
        workflow.isExternal,
        users,
      ),
      'system-column-progress': `${progress}%`,
      'system-column-step': stepLabel,
      'system-column-performer': getPerformersDisplayName(
        workflow.selectedUsers,
        users,
        groups,
        deletedGroupFallbackTemplate,
      ),
    };

    const fieldsMap = new Map<string, ITableViewFields>();
    workflow.fields?.forEach((f) => fieldsMap.set(f.apiName, f));

    const row = headerKeys.map((key) => {
      if (ALL_SYSTEM_FIELD_NAMES.includes(key)) {
        return systemValues[key];
      }
      const field = fieldsMap.get(key);
      return getOptionalFieldValue(field, timezone, users, groups);
    });
    bodyRows.push(row);
  });

  return [headerRow, ...bodyRows];
}

export async function buildWorkflowsXlsxBuffer(rows: string[][]) {
  const exceljs = await import('exceljs');
  const workbook = new exceljs.Workbook();
  const sheet = workbook.addWorksheet('Workflows');
  rows.forEach((cells) => {
    sheet.addRow(cells);
  });
  return workbook.xlsx.writeBuffer();
}

export function downloadWorkflowsExcel(
  buffer: BlobPart,
  filename = WORKFLOWS_XLSX_DEFAULT_FILENAME,
): void {
  const blob = new Blob([buffer], { type: WORKFLOWS_XLSX_MIME });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
