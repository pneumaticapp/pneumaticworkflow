import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IEditTeamUserRequest {
  managerId?: number | null;
  subordinatesIds?: number[];
}

export function editTeamUser(id: number, body: IEditTeamUserRequest) {
  return commonRequest<any>(
    `/accounts/users/${id}`,
    {
      data: mapRequestBody(body),
      method: 'PATCH',
    },
    { shouldThrow: true },
  );
}
