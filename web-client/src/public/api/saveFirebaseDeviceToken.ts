import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export interface ISaveFirebaseDeviceTokenResponse {
  user: number;
  token: string;
}

export function saveFirebaseDeviceToken(token: string) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<ISaveFirebaseDeviceTokenResponse>(
    urls.fcmDevice,
    {
      method: 'POST',
      body: mapRequestBody({ token }),
    },
    {
      shouldThrow: false,
    },
  );
}
