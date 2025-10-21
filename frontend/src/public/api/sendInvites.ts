import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { ETimeouts } from '../constants/defaultValues';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { UserInvitePayload } from '../redux/team/types';

interface InviteFailed {
  email: string;
}

export interface InviteResponse {
  alreadyAccepted: InviteFailed[];
}

export type TSendInvitesRequestBody = { [key: string]: string }[];

export function sendInvites(users: UserInvitePayload[], currentUrl: string) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<InviteResponse>(
    urls.sendInvites,
    {
      method: 'POST',
      data: mapRequestBody({ users }),
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
