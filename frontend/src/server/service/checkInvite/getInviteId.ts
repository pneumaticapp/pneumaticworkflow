import { Response } from 'express';
import * as request from 'request';
import { parse as parseQs } from 'querystring';

import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { ERoutes } from '../../../public/constants/routes';
import { isObject } from '../../../public/utils/mappers';
import { UserInviteResponse, ErrorCode } from './types';

const {
  api: { urls },
} = getConfig();

export const getInviteId = async (url: string, res: Response, options: request.CoreOptions) => {
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