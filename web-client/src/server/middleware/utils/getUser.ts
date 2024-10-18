import { Request } from 'express';

import { identifyAppPartOnServer } from '../../../public/utils/identifyAppPart/identifyAppPartOnServer';
import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';
import { getAuthHeader } from '../../utils/getAuthHeader';
import { IAuthenticatedUser } from '../../utils/types';

export async function getUser(req: Request, token: string, userAgent?: string) {
  try {
    const appPart = identifyAppPartOnServer(req);
    const headers = getAuthHeader({ token, appPart, userAgent });
    const user = await serverApi.get<IAuthenticatedUser>(
      'getUser',
      {
        headers,
        json: true,
      },
      true,
    );

    return user;
  } catch (error) {
    logger.error('failed to get user context: ', error);

    throw error;
  }
}
