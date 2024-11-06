import { commonRequest } from './commonRequest';
import { TForgotPassword } from '../redux/auth/actions';
import { mapRequestBody } from '../utils/mappers';

export function resetPassword(body: TForgotPassword) {
  return commonRequest('resetPassword', {
    method: 'POST',
    body: mapRequestBody(body),
  }, {
    responseType: 'empty',
    type: 'local',
    shouldThrow: true,
  });
}
