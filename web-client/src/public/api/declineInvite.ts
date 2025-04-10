import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export function declineInvite(inviteId: string) {
  return commonRequest('declineInvite', {
    method: 'POST',
    data: mapRequestBody({ inviteId }),
    headers: { 'Content-Type': 'application/json' },
  }, {
    type: 'local', shouldThrow: true, responseType: 'empty',
  });
}
