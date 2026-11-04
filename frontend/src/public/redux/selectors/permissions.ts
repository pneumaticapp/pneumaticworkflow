import type { RootState } from '../store';
import { EPermissionObjectType } from '../../types/permissions';

export const getCanChangeWorkflow = (workflowId?: number) => (state: RootState) =>
  Boolean(workflowId && state.permissions[EPermissionObjectType.Workflow][workflowId]?.hasChange);

export const getPermissionsUserId = (state: RootState) => state.permissions.userId;
