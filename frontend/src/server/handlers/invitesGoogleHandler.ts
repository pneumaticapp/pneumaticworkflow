import { Request, Response } from 'express';
import { google } from 'googleapis';
import { getGoogleOauthClient } from '../service/getGoogleOauthClient';
import { logger } from '../../public/utils/logger';
import { ERoutes } from '../../public/constants/routes';
import { mapGoogleUserList } from '../mappers/mapGoogleUserList';
import { getPostMessageScript } from '../utils';

const scopes = ['https://www.googleapis.com/auth/admin.directory.user.readonly'];

export async function invitesGoogleHandler(req: Request, res: Response) {
  const auth = getGoogleOauthClient(ERoutes.InvitesGoogle);
  if (req.query.code) {
    let resultMessage = '';
    try {
      const { tokens } = await auth.getToken(req.query.code as string);
      auth.credentials = tokens;
      const service = google.admin({ version: 'directory_v1', auth });
      const { data } = await service.users.list({
        customer: 'my_customer',
        projection: 'full',
        viewType: 'domain_public',
      });

      resultMessage = JSON.stringify({ googleUsers: mapGoogleUserList(data) });
    } catch (err) {
      resultMessage = JSON.stringify({ errors: (err && err.errors) || [] });

      logger.error(err);
    }

    return res.send(getPostMessageScript(resultMessage));
  }

  const redirectUri = auth.generateAuthUrl({
    access_type: 'offline',
    scope: scopes.join(' '),
  });

  return res.redirect(redirectUri);
}
