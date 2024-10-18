import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IGetTokenResponse {
  token: string;
}

export function getToken(username: string, password: string) {
  return commonRequest<IGetTokenResponse>('jwtObtain', {
    method: 'POST',
    body: mapRequestBody({username, password}),
  }, {
    type: 'local',
    shouldThrow: true,
  });
}
