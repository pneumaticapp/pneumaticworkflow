import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { IAuthUser } from '../types/redux';

export function changePhotoProfile(changedProfileFields: Partial<IAuthUser>) {
  const { api: { urls } } = getBrowserConfigEnv();

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
