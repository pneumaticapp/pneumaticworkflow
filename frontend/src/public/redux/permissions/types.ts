import type {
  EPermissionObjectType,
  IObjectPermissionResponseItem,
  TObjectPermissionsById,
} from '../../types/permissions';

export type TPermissionsStore = {
  [objType in EPermissionObjectType]: TObjectPermissionsById;
} & {
  userId: number | null;
};

export interface ILoadObjectPermissionsPayload {
  objType: EPermissionObjectType;
  objIds: number[];
}

export interface ISetObjectPermissionsPayload {
  objType: EPermissionObjectType;
  permissions: IObjectPermissionResponseItem[];
}
