import { EPermissionObjectType, IObjectPermissionResponseItem } from '../../types/permissions';

export interface ILoadObjectPermissionsPayload {
  objType: EPermissionObjectType;
  objIds: number[];
}

export interface ISetObjectPermissionsPayload {
  objType: EPermissionObjectType;
  permissions: IObjectPermissionResponseItem[];
}
