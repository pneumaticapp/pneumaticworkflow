import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IUpdateUserRequest {
  firstName: string;
  lastName: string;
  phone: string;
  dateFmt: string;
}

export type TUpdateUserMappedResponse = IUpdateUserRequest;

export interface IUpdateUserResponse {
  first_name: string;
  last_name: string;
  phone: string;
}

export function editProfile(body: IUpdateUserRequest) {

  return commonRequest<IUpdateUserResponse>(
    'editProfile',
    {
      body: mapRequestBody(body),
      method: 'PUT',
    });
}
