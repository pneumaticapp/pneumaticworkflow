import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { ETimeouts } from '../constants/defaultValues';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IUserInvite } from '../types/team';

interface IInviteFailed {
  email: string;
  is_staff: boolean;
}

export interface IInviteResponse {
  alreadyAccepted: IInviteFailed[];
}

export type TSendInvitesRequestBody = { [key: string]: string }[];

export function sendInvites(users: IUserInvite[], currentUrl: string) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IInviteResponse>(
    urls.sendInvites,
    {
      method: 'POST',
      body: mapRequestBody({ users }),
      headers: {
        'Content-Type': 'application/json',
        'X-Current-Url': currentUrl,
      },
    },
    {
      type: 'local',
      shouldThrow: true,
      timeOut: ETimeouts.Long,
    },
  );
}
