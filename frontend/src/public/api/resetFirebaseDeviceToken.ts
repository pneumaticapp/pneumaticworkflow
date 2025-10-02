import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export function resetFirebaseDeviceToken(token: string) {
  const { api: { urls }} = getBrowserConfigEnv();

  const url = urls.fcmDeviceToken.replace(":token", token);

  return commonRequest(
    url,
    {
      method: 'DELETE',
    },
    {
      shouldThrow: false,
      responseType: "empty",
    },
  );
}
