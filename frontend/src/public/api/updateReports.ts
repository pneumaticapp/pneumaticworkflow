import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';

export interface IUpdateReportsRequest {
  reportIds: number[];
}

export function updateReports(id: number, body: IUpdateReportsRequest) {
  return commonRequest<any>(
    `/accounts/users/${id}/set-reports`,
    {
      data: mapRequestBody(body),
      method: 'POST',
    }
  );
}
