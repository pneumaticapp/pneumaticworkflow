import * as request from 'request';
import { parse as parseQs } from 'querystring';
import { EOAuthType } from '../../../public/types/auth';
import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { ERoutes } from '../../../public/constants/routes';
import { IApiOAuthProfileResponse, mapOAuthProfile } from '../../mappers';
import { IUserInviteResponse } from '../../../public/types/team';
import { mergePaths } from '../../../public/utils/urls';

const { api: { urls }} = getConfig();

export const enum EProfile {
  Invite = 'invite',
}

type TProfileType = EOAuthType | EProfile;

const OAUTH_MAP_URLS: {[key in TProfileType]: string} = {
  [EOAuthType.Microsoft]: urls.googleAuth,
  [EOAuthType.Google]: urls.googleAuth,
  [EOAuthType.SSO]: urls.googleAuth,
  [EProfile.Invite]: urls.getInvite,
};

export const getProfileRequestCreator = <T>(expectedType: TProfileType) => async (
  type: TProfileType | null,
  url: string,
  onError: (e: Error) => void,
  options: request.CoreOptions,
) => {
  if (expectedType !== type) {
    return {} as Partial<T>;
  }

  try {
    const id = url.split('/').slice(-1)[0];
    const {token} = parseQs(id.slice(1));
    if (token) {
      const result = await serverApi.get<T>(
        `${OAUTH_MAP_URLS[type]}?token=${token}`,
        options,
      );

      return result as Partial<T>;
    }

    if (id) {
      const result = await serverApi.get<T>(
        [OAUTH_MAP_URLS[type], id].reduce(mergePaths),
        options,
      );

      return result;
    }
  } catch (err) {
    onError(err);
  }

  return {} as Partial<T>;
};

export const getGoogleInfo = getProfileRequestCreator<IApiOAuthProfileResponse>(EOAuthType.Google);
export const getInviteInfo = getProfileRequestCreator<IUserInviteResponse>(EProfile.Invite);

export function getProfileType(url: string): TProfileType | null {
  switch (true) {
    case (url.includes(ERoutes.SignUpGoogle)):
      return EOAuthType.Google;
    case (url.includes(ERoutes.SignUpInvite)):
      return EProfile.Invite;
    default:
      return null;
  }
}

export async function mapAuthProfiles(
  url: string,
  onError: (e: Error) => void,
  options: request.CoreOptions,
) {
  const type = getProfileType(url);

  return {
    googleAuthUserInfo: mapOAuthProfile(await getGoogleInfo(type, url, onError, options)),
    invitedUser: await getInviteInfo(type, url, onError, options),
  };
}
