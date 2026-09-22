import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EPermissionObjectType, IObjectPermissionResponseItem } from '../types/permissions';

export interface IGetUserObjectPermissionsConfig {
  objType: EPermissionObjectType;
  objIds: number[];
}

/** Ids that no longer exist come back with every permission set to false. */
export function getUserObjectPermissions({ objType, objIds }: IGetUserObjectPermissionsConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const params = new URLSearchParams({
    obj_type: objType,
    obj_ids: objIds.join(','),
  });

  return commonRequest<IObjectPermissionResponseItem[]>(
    `${urls.getUserObjectPermissions}?${params}`,
    {},
    { shouldThrow: true },
  );
}
