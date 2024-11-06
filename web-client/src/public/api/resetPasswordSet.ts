import { commonRequest } from './commonRequest';
import { IConfirmResetPassword } from '../redux/auth/actions';
import { mapRequestBody } from '../utils/mappers';

export interface IResetPasswordSetResponse {
  token: string;
}

export function resetPasswordSet(body: IConfirmResetPassword) {
  return commonRequest<IResetPasswordSetResponse>('resetPasswordSet', {
    method: 'POST',
    body: mapRequestBody(body),
  }, {
    type: 'local',
  });
}
