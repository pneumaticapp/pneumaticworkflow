import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { IUserResponse } from '../types/user';

export interface IVacationActivateRequest {
  substituteUserIds: number[];
  vacationStartDate?: string | null;
  vacationEndDate?: string | null;
  absenceStatus?: string;
}

export function activateVacation(
  body: IVacationActivateRequest,
  userId?: number,
) {
  const urls = getBrowserConfigEnv().api.urls as Record<string, string>;
  const url = userId 
    ? urls.vacationUserActivate.replace(':id', String(userId)) 
    : 'vacationActivate';

  return commonRequest<IUserResponse>(
    url,
    {
      data: mapRequestBody(body),
      method: 'POST',
    },
  );
}

export function deactivateVacation(userId?: number) {
  const urls = getBrowserConfigEnv().api.urls as Record<string, string>;
  const url = userId 
    ? urls.vacationUserDeactivate.replace(':id', String(userId)) 
    : 'vacationDeactivate';

  return commonRequest<IUserResponse>(
    url,
    {
      method: 'DELETE',
    },
  );
}
