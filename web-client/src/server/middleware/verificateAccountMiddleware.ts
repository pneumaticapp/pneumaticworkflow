import { Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { logger } from '../../public/utils/logger';
import { serverApi } from '../utils';

export async function verificateAccountMiddleware(req: Request, res: Response) {
  try {
    const { token } = req.query;
    const url = ERoutes.AccountVerification.replace(':token', token as string);
    await serverApi.get(url, {}, true);
  } catch (e) {
    logger.error(e);
  }

  return res.redirect(ERoutes.Login);
}
