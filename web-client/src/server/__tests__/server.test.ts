const utils = jest.requireActual('../../public/utils/getConfig');

jest.mock('mini-css-extract-plugin', () => {
  const plugin = () => {};
  plugin.loader = {};

  return plugin;
});

jest.mock('webpack', () => {
  const plugin = () => {};
  plugin.HotModuleReplacementPlugin = () => {};
  plugin.DefinePlugin = () => {};

  return plugin;
});

jest.mock('fork-ts-checker-webpack-plugin', () => {
  const plugin = () => {};
  plugin.loader = {};

  return plugin;
});
const getConfig = jest.fn();
jest.mock('../../public/utils/getConfig', () => ({
  getConfig,
}));
let mockConfig: any = { api: { urls: {} } };
jest.mock('../utils/request');
jest.mock('express');
jest.mock('webpack-dev-middleware');
jest.mock('webpack-hot-middleware');
jest.mock('../handlers/mainHandler');
jest.mock('../middleware/authMiddleware');
jest.mock('../../public/utils/getConfig', () => ({
  getConfig: () => mockConfig,
}));
jest.mock('../../../webpack.config.js');

import * as express from 'express';
import { initServer } from '../server';

const app: any = {
  use: jest.fn(),
  set: jest.fn(),
  get: jest.fn(),
  patch: jest.fn(),
  post: jest.fn(),
  listen: jest.fn(),
  delete: jest.fn(),
};
const router: any = {
  get: jest.fn(),
};

describe('server', () => {
  describe('initServer', () => {
    beforeEach(() => {
      jest.resetAllMocks();
      jest.resetModules();
      (express as unknown as jest.Mock).mockReturnValueOnce(app);
      (express.Router as unknown as jest.Mock).mockReturnValueOnce(router);
      mockConfig = { ...utils.getConfig(), ...mockConfig };
    });

    it('запускает сервер для продакшн окружения', () => {
      const log = jest.spyOn(console, 'info');

      initServer();
      const appListenCallback = app.listen.mock.calls[0][1];
      appListenCallback();

      expect(app.use).toHaveBeenCalledTimes(6);
      expect(app.get).toHaveBeenCalledTimes(9);
      expect(log).toHaveBeenCalledWith('App listening on port 8000');
    });

    it('возвращает порт 8000, если не указан в конфиге', () => {
      const log = jest.spyOn(console, 'info');
      mockConfig = { api: {}, port: undefined };

      initServer();
      const [appListenPort, appListenCallback] = app.listen.mock.calls[0];
      appListenCallback();

      expect(appListenPort).toEqual(8000);
      expect(log).toHaveBeenCalledWith('App listening on port 8000');
    });

    it('запускает сервер для дев окружения', () => {
      initServer();
      expect(app.use).toHaveBeenCalledTimes(6);
      expect(app.get).toHaveBeenCalledTimes(9);
    });
  });
});
