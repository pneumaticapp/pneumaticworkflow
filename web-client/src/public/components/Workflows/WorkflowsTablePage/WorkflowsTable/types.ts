import { IWorkflowClient } from '../../../../types/workflow';

export type TableColumns = {
  workflow: IWorkflowClient;
  starter: IWorkflowClient;
  progress: IWorkflowClient;
  step: IWorkflowClient;
  performer: IWorkflowClient;
};
