import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import { IGroup } from '../../redux/team/types';

export function getGroup(id: Pick<IGroup, 'id'>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.group.replace(':id', id);

  return commonRequest<IGroup>(url, {}, { shouldThrow: true });
}
