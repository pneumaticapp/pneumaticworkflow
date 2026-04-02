import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IEditTeamUserRequest {
  managerId: number | null;
}

export function editTeamUser(id: number, body: IEditTeamUserRequest) {
  if (body.managerId === null) {
    return commonRequest<any>(
      `/accounts/users/${id}/remove-manager`,
      { method: 'POST' }
    );
  }

  return commonRequest<any>(
    `/accounts/users/${id}/set-manager`,
    {
      data: mapRequestBody(body),
      method: 'POST',
    }
  );
}
