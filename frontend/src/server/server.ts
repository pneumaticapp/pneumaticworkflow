/* eslint-disable import/no-extraneous-dependencies */
import * as path from 'path';
import * as express from 'express';
import * as webpack from 'webpack';
import * as devMiddleware from 'webpack-dev-middleware';
import * as hotMiddleware from 'webpack-hot-middleware';

import { mainHandler, oAuthHandler, apiProxy } from './handlers';
import { authMiddleware, verificateAccountMiddleware, forwardForSubdomain } from './middleware';
import { getConfig, serverConfigToBrowser } from '../public/utils/getConfig';
import { ERoutes } from '../public/constants/routes';
import { setPublicAuthCookie } from './utils/cookie';
import { getUserPublic } from './middleware/utils/getUserPublic';
import { mapToCamelCase } from '../public/utils/mappers';
import { SSOProvider } from './types';

const webpackConfig = require('../../webpack.config');

const { NODE_ENV = 'development'} = process.env;
const devMode = NODE_ENV !== 'production';

const isSSOAuth = process.env.SSO_AUTH !== 'no';
const envSSOProvider = process.env.SSO_PROVIDER;


const {
  api: { urls },
} = getConfig();

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

  const formsRouter = express.Router();
  formsRouter.get('/', (_, res) => res.redirect(301, mainPage));
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
  app.get(ERoutes.AccountVerificationLink, verificateAccountMiddleware);
  app.get(ERoutes.OAuthGoogle, oAuthHandler(urls.getGoogleAuthUri, urls.getGoogleAuthToken));
  app.get(ERoutes.OAuthMicrosoft, oAuthHandler(urls.getMicrosoftAuthUri, urls.getMicrosoftAuthToken));

  if (isSSOAuth && envSSOProvider === SSOProvider.Auth0) { 
    app.get(ERoutes.OAuthSSOAuth0, oAuthHandler(urls.getSSOAuthUri, urls.getSSOAuthToken));
  }

  if (isSSOAuth && envSSOProvider === SSOProvider.Okta) {
    app.get(ERoutes.OAuthSSOOkta, oAuthHandler(urls.getSSOOktaUri, urls.getSSOOktaToken));
  }

  app.get('*', authMiddleware);
  app.get('*', mainHandler);

  app.listen(port, () => {
    console.info(`App listening on port ${port}`);
  });
}
