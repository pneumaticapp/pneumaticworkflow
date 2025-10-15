import { ITableViewFields } from '../../../../types/template';
import { IWorkflowClient } from '../../../../types/workflow';

export type TableColumns = {
  workflow: IWorkflowClient;
  templateName: IWorkflowClient;
  starter: IWorkflowClient;
  progress: IWorkflowClient;
  step: IWorkflowClient;
  performer: IWorkflowClient;
} & {
  [key: string]: ITableViewFields;
};

export type TSystemField = {
  apiName: string;
  name: string;
  isDisabled: boolean;
  hasNotTooltip: boolean;
};
