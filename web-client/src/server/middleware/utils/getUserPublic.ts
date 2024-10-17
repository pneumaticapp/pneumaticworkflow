import { Request } from 'express';

import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';
import { getAuthHeader } from '../../utils/getAuthHeader';
import { IAuthenticatedUser } from '../../utils/types';
import { EAppPart } from '../../../public/utils/identifyAppPart/types';

export async function getUserPublic(req: Request, token: string, userAgent?: string) {
  try {
    const headers = getAuthHeader({ token, appPart: EAppPart.PublicFormApp, userAgent });
    const user = await serverApi.get<IAuthenticatedUser>(
      'getPublicAccount',
      {
        headers,
        json: true,
      },
      true,
    );

    return user;
  } catch (error) {
    logger.error('failed to get account context: ', error);

    throw error;
  }
}
