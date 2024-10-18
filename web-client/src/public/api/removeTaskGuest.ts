import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function removeTaskGuest(taskId: number, guestEmail: string) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest(
    urls.removeTaskGuest.replace(':id', String(taskId)),
    {
      method: 'POST',
      body: mapRequestBody({ email: guestEmail }),
    },
    {
      responseType: 'empty',
      shouldThrow: true,
    },
  );
}
