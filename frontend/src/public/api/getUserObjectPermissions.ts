import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EPermissionObjectType, IObjectPermissionResponseItem } from '../types/permissions';

export interface IGetUserObjectPermissionsConfig {
  objType: EPermissionObjectType;
  objIds: number[];
}

/**
 * Effective permissions of the current user on the given objects.
 *
 * The endpoint takes query params, not a body: `?obj_type=workflow&obj_ids=1,2,3`.
 * Ids that no longer exist come back with every permission set to false instead of failing
 * the whole batch, so the caller maps the answer by id and keeps the rest of the list.
 */
export function getUserObjectPermissions({ objType, objIds }: IGetUserObjectPermissionsConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const queryString = `obj_type=${objType}&obj_ids=${objIds.join(',')}`;

  return commonRequest<IObjectPermissionResponseItem[]>(
    `${urls.userObjectPermissions}?${queryString}`,
    {},
    { shouldThrow: true },
  );
}
