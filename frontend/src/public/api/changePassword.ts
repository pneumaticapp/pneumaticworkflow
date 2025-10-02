import { commonRequest } from './commonRequest';
import { TChangePassword } from '../redux/auth/actions';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IChangePasswordResponse {
  token: string;
}

export function changePassword(body: TChangePassword) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<IChangePasswordResponse>(urls.changePassword, {
    method: 'POST',
    data: mapRequestBody(body),
  }, {
    type: 'local',
    shouldThrow: true,
  });
}
