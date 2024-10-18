import { commonRequest } from './commonRequest';
import { IUserRegister } from '../redux/auth/actions';
import { mapRequestBody } from '../utils/mappers';
import { IUserUtm } from '../views/user/utils/utmParams';

export interface IRegisterUserResponse {
  token: string;
}

export function registerUser(user: IUserRegister, utmParams?: IUserUtm, captcha?: string) {
  return commonRequest<IRegisterUserResponse>('registerUrl', {
    method: 'POST',
    body: mapRequestBody({ ...user, ...utmParams, captcha }),
    headers: {
      'Content-Type': 'application/json',
    },
  }, {
    type: 'local',
    shouldThrow: true,
  });
}
