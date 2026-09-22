export enum EPermissionObjectType {
  Workflow = 'workflow',
}

export interface IObjectPermission {
  hasView: boolean;
  hasChange: boolean;
}

export interface IObjectPermissionResponseItem extends IObjectPermission {
  id: number;
}

export type TObjectPermissionsById = Record<number, IObjectPermission>;
