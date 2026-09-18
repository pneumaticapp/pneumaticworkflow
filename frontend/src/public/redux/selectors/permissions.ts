import { IApplicationState } from '../../types/redux';
import { EPermissionObjectType } from '../../types/permissions';

export const getCanChangeWorkflow = (workflowId?: number) => (state: IApplicationState) =>
  Boolean(workflowId && state.permissions[EPermissionObjectType.Workflow][workflowId]?.hasChange);
