import { Response } from 'express';
import * as request from 'request';
import { parse as parseQs } from 'querystring';
import { EOAuthType } from '../../../public/types/auth';
import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { ERoutes } from '../../../public/constants/routes';
import { IApiOAuthProfileResponse, mapOAuthProfile } from '../../mappers';
import { IUserInviteResponse } from '../../../public/types/team';
import { mergePaths } from '../../../public/utils/urls';
import { isObject } from '../../../public/utils/mappers';

const {
  api: { urls },
} = getConfig();

export function getProfileType(url: string): TProfileType | null {
  switch (true) {
    case url.includes(ERoutes.SignUpGoogle):
      return EOAuthType.Google;
    case url.includes(ERoutes.SignUpInvite):
      return EProfile.Invite;
    default:
      return null;
  }
}

export const getProfileRequestCreator = <T>(expectedType: TProfileType) => {
  return async (type: TProfileType | null, url: string, res: Response, options: request.CoreOptions) => {
    const data: Partial<T> = {};
    if (expectedType !== type) return data;

    try {
      const id = url.split('/').slice(-1)[0];
      const { token } = parseQs(id.slice(1));

      if (token) {
        const result = await serverApi.get<T>(`${OAUTH_MAP_URLS[type]}?token=${token}`, options);
        return result as Partial<T>;
      }

      if (id) {
        const result = await serverApi.get<T>([OAUTH_MAP_URLS[type], id].reduce(mergePaths), options);
        return result;
      }
    } catch (err) {
      if (isObject(err) && 'code' in err) {
        if (err.code === EErrorCode.Validation) return res.redirect(ERoutes.ExpiredInvite);
        if (err.code === EErrorCode.Accepted) return res.redirect(ERoutes.Main);
      }
      return res.redirect(ERoutes.Register);
    }

    return data;
  };
};

export const getGoogleInfo = getProfileRequestCreator<IApiOAuthProfileResponse>(EOAuthType.Google);
export const getInviteInfo = getProfileRequestCreator<IUserInviteResponse>(EProfile.Invite);

export async function mapAuthProfiles(url: string, res: Response, options: request.CoreOptions) {
  const type = getProfileType(url);
  const googleInfo = await getGoogleInfo(type, url, res, options);
  const invitedUser = await getInviteInfo(type, url, res, options);

  if (!invitedUser || !googleInfo) return null;

  return {
    googleAuthUserInfo: mapOAuthProfile(googleInfo || undefined),
    invitedUser,
  };
}

export const enum EProfile {
  Invite = 'invite',
}

type TProfileType = EOAuthType | EProfile;

const OAUTH_MAP_URLS: { [key in TProfileType]: string } = {
  [EOAuthType.Microsoft]: urls.googleAuth,
  [EOAuthType.Google]: urls.googleAuth,
  [EOAuthType.SSO]: urls.googleAuth,
  [EProfile.Invite]: urls.getInvite,
};

const enum EErrorCode {
  Validation = 'validation_error',
  Accepted = 'invite_already_accepted',
}
