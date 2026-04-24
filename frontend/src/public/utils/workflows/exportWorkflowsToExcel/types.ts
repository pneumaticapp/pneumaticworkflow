import { IWorkflowClient } from '../../../types/workflow';
import { ITableViewFields } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { IGroup } from '../../../redux/team/types';

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
