import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { TUserInvited } from '../types/user';

export interface IRegisterUserResponse {
  token: string;
}

export function acceptInvite(id: string, body: TUserInvited) {
  const { api: { urls }} = getBrowserConfigEnv();

  return commonRequest<IRegisterUserResponse>(
    urls.acceptInvite.replace(':id', id),
    {
      method: 'POST',
      data: mapRequestBody(body as unknown as {[key: string]: string}),
    },
    {
      type: 'local',
      shouldThrow: true,
    },
  );
}
