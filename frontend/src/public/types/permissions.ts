/** Object types the permissions API can answer for (backend PermissionObjectType). */
export enum EPermissionObjectType {
  Workflow = 'workflow',
}

/** Effective permissions of the current user on a single object. */
export interface IObjectPermission {
  hasView: boolean;
  hasChange: boolean;
}

/** One entry of the permissions API response. */
export interface IObjectPermissionResponseItem extends IObjectPermission {
  id: number;
}

export type TObjectPermissionsById = Record<number, IObjectPermission>;
