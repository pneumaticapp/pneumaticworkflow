import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { IGroup } from '../../types/team';
import { mapRequestBody } from '../../utils/mappers';

export function createGroup(group: IGroup) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGroup[]>(
    urls.groups,
    {
      method: 'POST',
      data: mapRequestBody(group),
    },
    { shouldThrow: true },
  );
}
