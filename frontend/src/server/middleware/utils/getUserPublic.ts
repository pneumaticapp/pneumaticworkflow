import { Request } from 'express';

import {
  logServerError,
  errorToString,
  EXPECTED_AUTH_ERROR,
  LOG_PREFIX_ACCOUNT_CONTEXT,
} from '../../utils/expectedErrors';
import { serverApi } from '../../utils';
import { getAuthHeader } from '../../utils/getAuthHeader';
import { IAuthenticatedUser } from '../../utils/types';
import { EAppPart } from '../../../public/utils/identifyAppPart/types';
import { logger } from '../../../public/utils/logger';

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
    if (errorToString(error).includes(EXPECTED_AUTH_ERROR)) {
      logger.info(LOG_PREFIX_ACCOUNT_CONTEXT, error);
    } else {
      logServerError(LOG_PREFIX_ACCOUNT_CONTEXT, error);
    }

    throw error;
  }
}
