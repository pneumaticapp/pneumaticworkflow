import type { IRunWorkflow } from '../../types/workflow';

export interface IStoreRunWorkflowModal {
  workflow: IRunWorkflow | null;
  isOpen: boolean;
  isWorkflowStarting: boolean;
}
