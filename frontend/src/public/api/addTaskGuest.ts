import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import type { TUserListItem } from '../types/user';

export function addTaskGuest(taskId: number, guestEmail: string) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<TUserListItem>(
    urls.addTaskGuest.replace(':id', String(taskId)),
    {
      method: 'POST',
      data: mapRequestBody({ email: guestEmail }),
    },
    {
      shouldThrow: true,
    },
  );
}
