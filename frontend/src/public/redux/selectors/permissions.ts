import { IApplicationState } from '../../types/redux';
import { EPermissionObjectType, IObjectPermission } from '../../types/permissions';

/**
 * Undefined while the answer for that object has not arrived yet — the caller decides what an
 * unknown permission means, and for controls it means "hide until we know".
 */
export const getObjectPermission =
  (objType: EPermissionObjectType, objId?: number) =>
  (state: IApplicationState): IObjectPermission | undefined =>
    objId ? state.permissions[objType][objId] : undefined;

export const getCanChangeWorkflow = (workflowId?: number) => (state: IApplicationState) =>
  Boolean(getObjectPermission(EPermissionObjectType.Workflow, workflowId)(state)?.hasChange);
