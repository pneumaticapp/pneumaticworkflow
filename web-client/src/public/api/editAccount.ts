import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { TAccountLeaseLevel } from '../types/user';

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

export function editAccount(settings: IUpdateAccountRequest, leaseLevel: TAccountLeaseLevel) {
  return commonRequest<IUpdateAccountResponse>(
    'editAccount',
    {
      data: mapRequestBody({
        name: settings.name,
        ...(leaseLevel !== "tenant" && {logoSm: settings.logoSm || null}),
        ...(leaseLevel !== "tenant" && {logoLg: settings.logoLg || null}),
      }),
      method: 'PUT',
    });
}
