import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { TUserListItem } from '../types/user';

export function addTaskGuest(taskId: number, guestEmail: string) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<TUserListItem>(
    urls.addTaskGuest.replace(':id', String(taskId)),
    {
      method: 'POST',
      body: mapRequestBody({ email: guestEmail }),
    },
    {
      shouldThrow: true,
    },
  );
}
