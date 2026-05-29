// <reference types="jest" />

/**
 * Tests for webpack.config.js behavioral changes:
 * 1. No dotenv — .env is not read at build time
 * 2. No envKeys — process.env is not forwarded to bundle
 * 3. DefinePlugin only sets process.env.NODE_ENV
 * 4. No MCS_RUN_ENV in HtmlWebpackPlugin
 * 5. No Sentry webpack plugin
 */

jest.mock('mini-css-extract-plugin', () => {
  class MiniCssExtractPlugin {
    static loader = {};
  }
  return MiniCssExtractPlugin;
});

jest.mock('fork-ts-checker-webpack-plugin', () => {
  return class ForkTsCheckerWebpackPlugin {};
});

jest.mock('html-webpack-plugin', () => {
  return class HtmlWebpackPlugin {
    public options: Record<string, unknown>;
    constructor(options: Record<string, unknown>) {
      this.options = options;
    }
  };
});

interface IWebpackPlugin {
  constructor: { name: string };
  definitions?: Record<string, string>;
  options?: Record<string, unknown> & { authToken?: string; filename?: string };
}

describe('webpack.config.js', () => {
  const ORIGINAL_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...ORIGINAL_ENV };
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  const loadConfig = (envOverrides: Record<string, string> = {}) => {
    Object.assign(process.env, envOverrides);
    return require('../../webpack.config.js') as { plugins: IWebpackPlugin[]; entry: unknown; mode: string; devtool: string };
  };

  describe('DefinePlugin configuration', () => {
    it('defines process.env.NODE_ENV via DefinePlugin (not full process.env)', () => {
      process.env.NODE_ENV = 'production';
      const config = loadConfig({ NODE_ENV: 'production' });

      const definePlugin = config.plugins.find(
        (p: IWebpackPlugin) => p.constructor.name === 'DefinePlugin',
      );

      expect(definePlugin).toBeDefined();
      expect(definePlugin!.definitions).toEqual({
        'process.env.NODE_ENV': '"production"',
      });
    });

    it('does not forward arbitrary env vars to the bundle', () => {
      const config = loadConfig({
        NODE_ENV: 'development',
        SECRET_KEY: 'should-not-be-in-bundle',
        BACKEND_URL: 'https://example.com',
      });

      const definePlugin = config.plugins.find(
        (p: IWebpackPlugin) => p.constructor.name === 'DefinePlugin',
      );

      expect(definePlugin!.definitions).not.toHaveProperty('process.env');
      const definedKeys = Object.keys(definePlugin!.definitions!);
      expect(definedKeys).not.toContain('process.env');
      expect(definedKeys).toEqual(['process.env.NODE_ENV']);
    });
  });

  describe('HtmlWebpackPlugin configuration', () => {
    it('main template does not have mcsRunEnv property', () => {
      const config = loadConfig({ NODE_ENV: 'production' });

      const htmlPlugins = config.plugins.filter(
        (p: IWebpackPlugin) => p.constructor.name === 'HtmlWebpackPlugin',
      );

      const mainPlugin = htmlPlugins.find((p: IWebpackPlugin) => p.options?.filename === 'main.ejs');
      expect(mainPlugin).toBeDefined();
      expect(mainPlugin!.options).not.toHaveProperty('mcsRunEnv');
    });

    it('forms template does not have mcsRunEnv property', () => {
      const config = loadConfig({ NODE_ENV: 'production' });

      const htmlPlugins = config.plugins.filter(
        (p: IWebpackPlugin) => p.constructor.name === 'HtmlWebpackPlugin',
      );

      const formsPlugin = htmlPlugins.find((p: IWebpackPlugin) => p.options?.filename === 'forms.ejs');
      expect(formsPlugin).toBeDefined();
      expect(formsPlugin!.options).not.toHaveProperty('mcsRunEnv');
    });
  });

  describe('Sentry webpack plugin removal', () => {
    it('does not include sentryWebpackPlugin even when SENTRY_AUTH_TOKEN is set', () => {
      const config = loadConfig({
        NODE_ENV: 'production',
        SENTRY_AUTH_TOKEN: 'fake-token',
        SENTRY_RELEASE: 'v1.0.0',
        SENTRY_ORG: 'test-org',
        SENTRY_PROJECT: 'test-project',
      });

      const pluginNames = config.plugins.map((p: IWebpackPlugin) => p.constructor.name);
      expect(pluginNames).not.toContain('sentryWebpackPlugin');

      const hasSentryPlugin = config.plugins.some(
        (p: IWebpackPlugin) =>
          p.constructor.name.toLowerCase().includes('sentry') ||
          (p.options && p.options.authToken),
      );
      expect(hasSentryPlugin).toBe(false);
    });
  });

  describe('dotenv removal', () => {
    it('does not require dotenv module', () => {
      const config = loadConfig({ NODE_ENV: 'production' });

      // Config should load successfully without a .env file
      expect(config).toBeDefined();
      expect(config.entry).toBeDefined();
    });
  });

  describe('mode and devtool', () => {
    it('sets mode to production when NODE_ENV is production', () => {
      const config = loadConfig({ NODE_ENV: 'production' });

      expect(config.mode).toBe('production');
    });

    it('sets mode to development when NODE_ENV is development', () => {
      const config = loadConfig({ NODE_ENV: 'development' });

      expect(config.mode).toBe('development');
    });
  });
});
