import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IUpdateSubordinatesRequest {
  subordinates: number[];
}

export function updateSubordinates(id: number, body: IUpdateSubordinatesRequest) {
  return commonRequest<any>(
    `/accounts/users/${id}`,
    {
      data: mapRequestBody(body),
      method: 'PATCH',
    }
  );
}
