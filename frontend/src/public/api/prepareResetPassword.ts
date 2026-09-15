import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IPrepareResetPasswordResponse {
  showCaptcha: boolean;
}

export function prepareResetPassword() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IPrepareResetPasswordResponse>(
    urls.resetPasswordCaptcha,
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}
