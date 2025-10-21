import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import { IGroup } from '../../redux/team/types';

export function deleteGroup(id: Pick<IGroup, 'id'>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.group.replace(':id', id);

  return commonRequest<IGroup[]>(
    url,
    {
      method: 'DELETE',
    },
    { shouldThrow: true },
  );
}
