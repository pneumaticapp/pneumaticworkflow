import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import { IGroup } from '../../redux/team/types';
import { mapRequestBody } from '../../utils/mappers';

export function updateGroupApi(group: IGroup) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.group.replace(':id', group.id);

  return commonRequest<IGroup[]>(
    url,
    {
      method: 'PUT',
      data: mapRequestBody(group),
    },
    { shouldThrow: true },
  );
}
