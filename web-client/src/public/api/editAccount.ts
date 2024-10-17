import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { isTenant } from './isTenant';

export interface IUpdateAccountRequest {
  name: string;
  logoSm: string | null;
  logoLg: string | null;
}

export interface IUpdateAccountResponse {
  name: string;
}

export interface IUpdatedAccount {
  name: string;
}

export function editAccount(settings: IUpdateAccountRequest) {


  return commonRequest<IUpdateAccountResponse>(
    'editAccount',
    {
      body: mapRequestBody({
        name: settings.name,
        ...(!isTenant() && {logoSm: settings.logoSm || null}),
        ...(!isTenant() && {logoLg: settings.logoLg || null}),
      }),
      method: 'PUT',
    });
}
