import { Request, Response } from 'express';

import { ERoutes } from '../../public/constants/routes';
import { logServerError } from '../utils/expectedErrors';
import { serverApi } from '../utils';

export async function verificateAccountMiddleware(req: Request, res: Response) {
  try {
    const { token } = req.query;
    const url = ERoutes.AccountVerification.replace(':token', token as string);
    await serverApi.get(url, {}, true);
  } catch (error) {
    logServerError(error);
  }

  return res.redirect(ERoutes.Login);
}
