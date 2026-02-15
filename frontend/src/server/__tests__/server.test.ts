const utils = jest.requireActual('../../public/utils/getConfig');

jest.mock('mini-css-extract-plugin', () => {
  class MiniCssExtractPlugin {}
  (MiniCssExtractPlugin as unknown as { loader: unknown }).loader = {};
  return MiniCssExtractPlugin;
});

jest.mock('webpack', () => {
  const webpackFn = Object.assign(() => ({}), {
    DefinePlugin: class DefinePlugin {},
    HotModuleReplacementPlugin: class HotModuleReplacementPlugin {},
  });
  return webpackFn;
});

jest.mock('fork-ts-checker-webpack-plugin', () => {
  const plugin = () => {};
  plugin.loader = {};
  return plugin;
});

let mockConfig: any;
jest.mock('../utils/request');
jest.mock('express');
jest.mock('webpack-dev-middleware');
jest.mock('webpack-hot-middleware');
jest.mock('../handlers/mainHandler');
jest.mock('../middleware/authMiddleware');
jest.mock('../../public/utils/getConfig', () => ({
  getConfig: () => mockConfig,
}));
jest.mock('../../../webpack.config.js', () => ({}));

let express: typeof import('express');
let app: any;
let router: any;

const createAppMock = () => ({
  use: jest.fn(),
  set: jest.fn(),
  get: jest.fn(),
  patch: jest.fn(),
  post: jest.fn(),
  listen: jest.fn(),
  delete: jest.fn(),
});

const createRouterMock = () => ({
  get: jest.fn(),
});

const initMockConfig = () => {
  const realConfig = utils.getConfig();
  return {
    ...realConfig,
    api: {
      ...realConfig.api,
      urls: realConfig.api?.urls || {},
    },
  };
};

const setupMocks = () => {
  express = jest.requireMock('express');
  app = createAppMock();
  router = createRouterMock();
  (express as unknown as jest.Mock).mockReturnValue(app);
  (express.Router as unknown as jest.Mock).mockReturnValue(router);
  
  if (!mockConfig || !mockConfig.api?.urls) {
    mockConfig = initMockConfig();
  }
  
  const getConfigMock = jest.requireMock('../../public/utils/getConfig');
  getConfigMock.getConfig = jest.fn(() => mockConfig);
};

describe('server', () => {
  const originalEnv = process.env;

  describe('initServer', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      jest.resetModules();
      process.env = { ...originalEnv };
      mockConfig = initMockConfig();
      setupMocks();
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    const setEnvAndGetInitServer = (env: Record<string, string | undefined>) => {
      Object.assign(process.env, env);
      jest.resetModules();
      setupMocks();
      return jest.requireActual('../server');
    };

    it('starts the server for the production environment', () => {
      const log = jest.spyOn(console, 'info');

      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'production',
        SSO_AUTH: 'no',
      });

      initServer();
      const appListenCallback = app.listen.mock.calls[0][1];
      appListenCallback();

      expect(app.use).toHaveBeenCalledTimes(4);
      expect(app.get).toHaveBeenCalledTimes(7);
      expect(log).toHaveBeenCalledWith('App listening on port 8000');
    });

    it('returns port 8000 if not specified in the config', () => {
      const log = jest.spyOn(console, 'info');
      mockConfig = { ...mockConfig, port: undefined };

      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'production',
        SSO_AUTH: 'no',
      });

      initServer();
      const [appListenPort, appListenCallback] = app.listen.mock.calls[0];
      appListenCallback();

      expect(appListenPort).toEqual(8000);
      expect(log).toHaveBeenCalledWith('App listening on port 8000');
    });

    it('starts the server for the development environment', () => {
      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'development',
        SSO_AUTH: 'no',
      });

      initServer();

      expect(app.use).toHaveBeenCalledTimes(6);
      expect(app.get).toHaveBeenCalledTimes(7);
    });

    it('adds Auth0 SSO route when SSO_AUTH is enabled and SSO_PROVIDER is Auth0', () => {
      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'production',
        SSO_AUTH: 'yes',
        SSO_PROVIDER: 'auth0',
      });

      initServer();

      expect(app.get).toHaveBeenCalledTimes(8);
    });

    it('adds Okta SSO route when SSO_AUTH is enabled and SSO_PROVIDER is Okta', () => {
      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'production',
        SSO_AUTH: 'yes',
        SSO_PROVIDER: 'okta',
      });

      initServer();
      
      expect(app.get).toHaveBeenCalledTimes(8);
    });

    it('does not add SSO routes when SSO_AUTH is disabled', () => {
      const { initServer } = setEnvAndGetInitServer({
        NODE_ENV: 'production',
        SSO_AUTH: 'no',
        SSO_PROVIDER: 'auth0',
      });

      initServer();

      expect(app.get).toHaveBeenCalledTimes(7);
    });
  });
});
