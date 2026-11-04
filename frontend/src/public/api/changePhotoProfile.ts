import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import type { TAuthUserResult } from '../types/user';

export function changePhotoProfile(changedProfileFields: Partial<TAuthUserResult>) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest(
    urls.editProfile,
    {
      method: 'PUT',
      data: mapRequestBody(changedProfileFields),
    },
    {
      shouldThrow: true,
    },
  );
}
