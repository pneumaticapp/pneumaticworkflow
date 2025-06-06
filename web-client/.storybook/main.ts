import type { StorybookConfig } from '@storybook/react-webpack5';
import path from 'path';
import MiniCssExtractPlugin from 'mini-css-extract-plugin';

const { NODE_ENV = 'development' } = process.env;
const devMode = NODE_ENV !== 'production';
const fontsDir = path.resolve(__dirname, '../src/public/assets');

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-webpack5-compiler-swc',
    '@storybook/addon-onboarding',
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@chromatic-com/storybook',
    '@storybook/addon-interactions',
    {
      name: '@storybook/addon-styling-webpack',
      options: {
        rules: [
          {
            test: /\.css$/,
            use: [
              devMode ? 'style-loader' : MiniCssExtractPlugin.loader,
              {
                loader: 'css-loader',
                options: {
                  modules: {
                    localIdentName: devMode 
                      ? '[path][name]__[local]--[hash:base64:5]' 
                      : '[local]--[hash:base64:5]',
                    getLocalIdent: (loaderContext, _, localName) => {
                      const { resourcePath } = loaderContext;
                      if (resourcePath.includes(fontsDir) || resourcePath.includes('node_modules')) {
                        return localName;
                      }
                    },
                  },
                },
              },
              'postcss-loader',
            ],
          },
          {
            test: /\.s[ac]ss$/i,
            use: [
              devMode ? 'style-loader' : MiniCssExtractPlugin.loader,
              'css-loader',
              'sass-loader'
            ],
          },
        ],
        plugins: devMode ? [] : [
          new MiniCssExtractPlugin({
            filename: 'styles/[name].[contenthash].css',
          }),
        ],
      },
    },
    'storybook-react-intl',
  ],
  framework: '@storybook/react-webpack5',
  docs: {
    autodocs: 'tag',
  },
};

export default config;