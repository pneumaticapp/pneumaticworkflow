import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IUpdateUserRequest {
  firstName: string;
  lastName: string;
  phone: string;
  dateFmt: string;
  managerId?: number | null;
}

export type TUpdateUserMappedResponse = IUpdateUserRequest;

export interface IUpdateUserResponse {
  first_name: string;
  last_name: string;
  phone: string;
}

export function editProfile(body: IUpdateUserRequest) {
  return commonRequest<IUpdateUserResponse>(
    '/accounts/user',
    {
      data: mapRequestBody(body),
      method: 'PUT',
    });
}

export function editProfileManager(managerId: number | null) {
  if (managerId === null) {
    return commonRequest<any>(
      '/accounts/user/remove-manager',
      { method: 'POST' }
    );
  }
  return commonRequest<any>(
    '/accounts/user/set-manager',
    {
      data: mapRequestBody({ managerId }),
      method: 'POST',
    }
  );
}
