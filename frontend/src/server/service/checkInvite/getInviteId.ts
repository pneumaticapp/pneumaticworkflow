import type { Response } from 'express';
import { parse as parseQs } from 'querystring';
import type { IHttpRequestOptions } from '../../utils';
import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { ERoutes } from '../../../public/constants/routes';
import { isObject } from '../../../public/utils/mappers';
import type { UserInviteResponse } from './types';
import { ErrorCode } from './types';

const {
  api: { urls },
} = getConfig();

export const getInviteId = async (url: string, res: Response, options?: IHttpRequestOptions) => {
  try {
    const id = url.split('/').slice(-1)[0];
    const { token } = parseQs(id.slice(1));

    if (token) {
      const result = await serverApi.get<UserInviteResponse>(`${urls.getInvite}?token=${token}`, options);
      return result as Partial<UserInviteResponse>;
    }
  } catch (err) {
    if (isObject(err) && 'code' in err) {
      if (err.code === ErrorCode.Validation) return res.redirect(ERoutes.ExpiredInvite);
      if (err.code === ErrorCode.Accepted) return res.redirect(ERoutes.Main);
    }
    return res.redirect(ERoutes.Register);
  }

  return {};
};
