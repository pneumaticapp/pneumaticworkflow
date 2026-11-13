import { commonRequest } from './commonRequest';
import type { TForgotPassword } from '../redux/auth/actions';
import { mapRequestBody } from '../utils/mappers';

export function resetPassword(body: TForgotPassword) {
  return commonRequest(
    'resetPassword',
    {
      method: 'POST',
      data: mapRequestBody(body),
    },
    {
      responseType: 'empty',
      type: 'local',
      shouldThrow: true,
    },
  );
}
