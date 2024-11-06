const webpack = require('webpack');
const path = require('path');
const dotenv = require('dotenv');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');
// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

const env = dotenv.config().parsed;
const { NODE_ENV = 'development', MCS_RUN_ENV = 'local' } = process.env;
const devMode = NODE_ENV !== 'production';
const fontsDir = path.resolve(__dirname, './src/public/assets');

const envKeys = Object.keys(Object.assign(env, process.env)).reduce((prev, next) => {
  prev[next] = JSON.stringify(env[next]);
  return prev;
}, {});

module.exports = {
  entry: {
    main: devMode ? ['webpack-hot-middleware/client?path=/__webpack_hmr&reload=true', './src/public/browser.tsx'] : './src/public/browser.tsx',
    forms: './src/public/forms.tsx',
  },
  output: {
    filename: devMode ? '[name].js' : '[name].[contenthash].js',
    path: path.resolve(__dirname, './public'),
    publicPath: '/static/',
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: 'ts-loader',
            options: {
              transpileOnly: true,
            },
          },
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              modules: {
                localIdentName: devMode ? '[path][name]__[local]--[hash:base64:5]' : '[local]--[hash:base64:5]',
                getLocalIdent: (loaderContext, _, localName) => {
                  const { resourcePath } = loaderContext;
                  if (resourcePath.includes(fontsDir) || resourcePath.includes('node_modules')) {
                    return localName;
                  }
                },
              },
              import: true,
            },
          },
          'postcss-loader'
        ],
      },
      {
        test: /\.s[ac]ss$/i,
        use: ['style-loader', 'css-loader', 'sass-loader'],
      },
      {
        test: /\.(jpe?g|png|gif|svg)$/i,
        use: {
          loader: 'file-loader',
          options: {
            name: '[path][name].[ext]',
          },
        },
      },
      {
        test: /\.(ttf|eot|woff|woff2)$/,
        use: {
          loader: 'file-loader',
          options: {
            name: 'fonts/[name].[ext]',
          },
        },
      },
    ],
  },
  plugins: [
    new webpack.DefinePlugin({
      'process.env': envKeys,
    }),
    new webpack.HotModuleReplacementPlugin(),
    new MiniCssExtractPlugin({
      filename: devMode ? '[name].css' : '[name].[contenthash].css',
    }),
    new HtmlWebpackPlugin({
      chunks: ['main'],
      filename: 'main.ejs',
      template: '!!raw-loader!./src/public/index.ejs',
      mcsRunEnv: MCS_RUN_ENV,
      removeComments: true,
      favicon: './src/public/assets/favicon.png',
    }),
    new HtmlWebpackPlugin({
      chunks: ['forms'],
      filename: 'forms.ejs',
      template: '!!raw-loader!./src/public/forms.ejs',
      mcsRunEnv: MCS_RUN_ENV,
      removeComments: true,
      favicon: './src/public/assets/favicon.png',
    }),
    new ForkTsCheckerWebpackPlugin(),
    // Uncomment to run Bundle Analyzer
    // new BundleAnalyzerPlugin(),
    {
      apply: (compiler) => {
        compiler.hooks.done.tap('DonePlugin', (stats) => {
          console.log('Compile is done!');

          // in case process not exited
          if (!devMode) {
            setTimeout(() => {
              process.exit(0);
            });
          }
        });
      },
    },
  ],
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  mode: NODE_ENV,
};





