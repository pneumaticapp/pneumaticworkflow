import { commonRequest } from './commonRequest';
import type { IUserRegister, IUserUtm } from '../types/user';
import { mapRequestBody } from '../utils/mappers';

export interface IRegisterUserResponse {
  token: string;
}

export function registerUser(user: IUserRegister, utmParams?: IUserUtm, captcha?: string) {
  return commonRequest<IRegisterUserResponse>(
    'registerUrl',
    {
      method: 'POST',
      data: mapRequestBody({ ...user, ...utmParams, captcha }),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}
