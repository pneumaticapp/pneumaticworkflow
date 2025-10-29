import { ITableViewFields } from '../../../../types/template';
import { IWorkflowClient } from '../../../../types/workflow';

export type TableColumns = {
  'system-column-workflow': IWorkflowClient;
  'system-column-templateName': IWorkflowClient;
  'system-column-starter': IWorkflowClient;
  'system-column-progress': IWorkflowClient;
  'system-column-step': IWorkflowClient;
  'system-column-performer': IWorkflowClient;
} & {
  [key: string]: ITableViewFields;
};

export type TSystemField = {
  apiName: string;
  name: string;
  isDisabled: boolean;
  hasNotTooltip: boolean;
};
