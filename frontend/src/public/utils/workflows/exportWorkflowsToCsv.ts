import { IWorkflowClient } from '../../types/workflow';
import { ITableViewFields, EExtraFieldType, ETemplateOwnerType } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { IGroup } from '../../redux/team/types';
import { getUserFullName, EXTERNAL_USER } from '../users';
import { getUserById } from '../../components/UserData/utils/getUserById';
import { toDateString } from '../dateTime';
import { getWorkflowProgress } from '../../components/Workflows/utils/getWorkflowProgress';

const CSV_QUOTE = '"';
const CSV_DOUBLE_QUOTE = '""';

function escapeCsvCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) {
    return '';
  }
  const str = String(value);
  const needsQuoting = /[",\r\n]/.test(str);
  if (needsQuoting) {
    return CSV_QUOTE + str.replace(/"/g, CSV_DOUBLE_QUOTE) + CSV_QUOTE;
  }
  return str;
}

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

export interface IExportWorkflowsToCsvConfig {
  workflows: IWorkflowClient[];
  users: TUserListItem[];
  groups: IGroup[];
  selectedFields: string[];
  optionalFieldsFromWorkflow?: ITableViewFields[];
  timezone?: string;
  headerLabels: Record<string, string>;
  multipleTasksLabel: string;
  /** Localized template for missing group in performers, use {id} placeholder for group ID */
  deletedGroupFallbackTemplate: string;
}

const SYSTEM_COLUMNS = [
  'system-column-workflow',
  'system-column-templateName',
  'system-column-starter',
  'system-column-progress',
  'system-column-step',
  'system-column-performer',
] as const;

export function buildWorkflowsCsvContent({
  workflows,
  users,
  groups,
  selectedFields,
  optionalFieldsFromWorkflow,
  timezone,
  headerLabels,
  multipleTasksLabel,
  deletedGroupFallbackTemplate,
}: IExportWorkflowsToCsvConfig): string {
  const headerKeys = selectedFields.length > 0
    ? selectedFields
    : [
      ...SYSTEM_COLUMNS,
      ...(optionalFieldsFromWorkflow ?? []).map((f) => f.apiName),
    ];

  const headers = headerKeys.map((key) => escapeCsvCell(headerLabels[key] ?? key));
  const rows: string[] = [headers.join(',')];

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

    const cells = headerKeys.map((key) => {
      if (SYSTEM_COLUMNS.includes(key as (typeof SYSTEM_COLUMNS)[number])) {
        return escapeCsvCell(systemValues[key]);
      }
      const field = fieldsMap.get(key);
      return escapeCsvCell(
        getOptionalFieldValue(field, timezone, users, groups),
      );
    });
    rows.push(cells.join(','));
  });

  return rows.join('\r\n');
}

const UTF8_BOM = '\uFEFF';

export function downloadWorkflowsCsv(csvContent: string, filename = 'workflows.csv'): void {
  const blob = new Blob([UTF8_BOM + csvContent], { type: 'text/csv;charset=utf-8' });
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
