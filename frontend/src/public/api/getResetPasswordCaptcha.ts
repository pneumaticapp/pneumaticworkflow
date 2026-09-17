import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IGetResetPasswordCaptchaResponse {
  showCaptcha: boolean;
}

export function getResetPasswordCaptcha() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGetResetPasswordCaptchaResponse>(
    urls.getResetPasswordCaptcha,
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}
