import type { IWorkflowClient } from '../../../types/workflow';
import type { ITableViewFields } from '../../../types/template';
import type { TUserListItem } from '../../../types/user';
import type { IGroup } from '../../../types/team';

export type TWorkflowExportFormat = 'xlsx' | 'csv';

export interface IExportWorkflowsToExcelConfig {
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
