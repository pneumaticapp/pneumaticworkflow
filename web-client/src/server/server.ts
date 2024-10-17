/* eslint-disable import/no-extraneous-dependencies */
import * as path from 'path';
import * as express from 'express';
import * as webpack from 'webpack';
import * as devMiddleware from 'webpack-dev-middleware';
import * as hotMiddleware from 'webpack-hot-middleware';

import { mainHandler } from './handlers';
import { authMiddleware, verificateAccountMiddleware } from './middleware';
import { getConfig, serverConfigToBrowser } from '../public/utils/getConfig';
import { oauthGoogleHandler } from './handlers/oauthGoogleHandler';
import { apiProxy } from './handlers/apiProxy';
import { ERoutes } from '../public/constants/routes';
import { invitesGoogleHandler } from './handlers/invitesGoogleHandler';
import { forwardForSubdomain } from './middleware/forwardForSubdomain';
import { setPublicAuthCookie } from './utils/cookie';
import { oauthMicrosoftHandler } from './handlers/oauthMicrosoftHandler';
import { oauthSSOHandler } from './handlers/oauthSSOHandler';
import { getUserPublic } from './middleware/utils/getUserPublic';
import { mapToCamelCase } from '../public/utils/mappers';

const webpackConfig = require('../../webpack.config');

const { NODE_ENV = 'development'} = process.env;
const devMode = NODE_ENV !== 'production';

export function initServer() {
  const webpackCompiler = webpack(webpackConfig);
  const app = express();
  const { host, port = 8000, formSubdomain, mainPage, firebase } = getConfig();

  if (devMode) {
    app.use(
      hotMiddleware(webpackCompiler, {
        path: '/__webpack_hmr',
      }),
    );

    app.use(
      devMiddleware(webpackCompiler),
    );
  }

  app.set('views', './public/');
  app.set('view engine', 'ejs');
  app.use(express.json());
  app.use('/assets/', express.static('assets'));
  app.use('/static/', express.static('public'));

  /* API PATH */
  app.post('/api/:path(*)', apiProxy('post'));
  app.get('/api/:path(*)', apiProxy('get'));
  app.patch('/api/:path(*)', apiProxy('patch'));
  app.delete('/api/:path(*)', apiProxy('delete'));

  app.get('/firebase-messaging-sw.js', (req, res) => {
    res.setHeader('Content-Type', 'text/javascript');

    return res.render(path.resolve(__dirname, '../public/firebase/firebase-messaging-sw.ejs'), {
      vapidKey: firebase.vapidKey,
      config: firebase.config,
      host,
    });
  });

  /* FORM SUBDOMAIN */
  const formsRouter = express.Router();
  formsRouter.get('/', (req, res) => res.redirect(301, mainPage));
  formsRouter.get('*', async (req, res) => {
    const token = /[^$/]+$/.exec(req.path)?.[0];
    let userPublic: any;

    try {
      if (token) {
        setPublicAuthCookie(req, res, token);
        userPublic = await new Promise((resolve) => {
          const publicContext = getUserPublic(req, token, req.headers['user-agent']);
          resolve(publicContext);
        }).then((value) => value);

        return res.render('forms', {
          env: process.env.MCS_RUN_ENV,
          config: JSON.stringify(serverConfigToBrowser()),
          user: JSON.stringify(mapToCamelCase(userPublic)),
        });
      }
    } catch (err) {
      return res.render('forms', {
        env: process.env.MCS_RUN_ENV,
        config: JSON.stringify(serverConfigToBrowser()),
        user: JSON.stringify(mapToCamelCase({})),
      });
    }

    return null;
  });
  app.use(forwardForSubdomain([formSubdomain], formsRouter));

  /* ACCOUNT VERIFICATION */
  app.get(ERoutes.AccountVerificationLink, verificateAccountMiddleware);

  app.get(ERoutes.OAuthGoogle, oauthGoogleHandler);
  app.get(ERoutes.OAuthMicrosoft, oauthMicrosoftHandler);
  app.get(ERoutes.OAuthSSO, oauthSSOHandler);

  app.get(ERoutes.InvitesGoogle, invitesGoogleHandler);

  app.get('*', authMiddleware);
  app.get('*', mainHandler);

  app.listen(port, () => {
    console.info(`App listening on port ${port}`);
  });
}
