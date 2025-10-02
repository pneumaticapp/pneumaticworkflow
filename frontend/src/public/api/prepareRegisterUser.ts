import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IPrepareRegisterUserResponse {
  showCaptcha: boolean;
}

export function prepareRegisterUser() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IPrepareRegisterUserResponse>(
    urls.registerUrl,
    {},
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}
