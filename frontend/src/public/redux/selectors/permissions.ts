import type { IApplicationState } from '../store';
import { EPermissionObjectType } from '../../types/permissions';

export const getCanChangeWorkflow = (workflowId?: number) => (state: IApplicationState) =>
  Boolean(workflowId && state.permissions[EPermissionObjectType.Workflow][workflowId]?.hasChange);

export const getPermissionsUserId = (state: IApplicationState) => state.permissions.userId;
