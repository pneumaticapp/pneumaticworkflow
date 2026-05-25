import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ICreateUserRequest, IUserResponse } from '../types/user';
import { mapRequestBody } from '../utils/mappers';

export function createUser(data: ICreateUserRequest) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IUserResponse>(
    urls.createUser,
    {
      data: mapRequestBody(data),
      method: 'POST',
    },
    { shouldThrow: true },
  );
}
