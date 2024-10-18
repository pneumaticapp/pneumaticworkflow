import { google } from 'googleapis';
import { mergePaths } from '../../../public/utils/urls';
import { getConfig } from '../../../public/utils/getConfig';
import { ERoutes } from '../../../public/constants/routes';

export function getGoogleOauthClient(route: ERoutes = ERoutes.OAuthGoogle) {
  const { host, google: { clientId, clientSecret } } = getConfig();

  return new google.auth.OAuth2(
    clientId,
    clientSecret,
    mergePaths(host, route),
  );
}
