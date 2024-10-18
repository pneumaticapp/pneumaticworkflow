const presetEnv = require("postcss-preset-env");
const postcssCustomMedia = require('postcss-custom-media');
const postcssMixins = require('postcss-mixins');
const postcssNested = require('postcss-nested');
const postcssImport = require('postcss-import');
const postcssComment = require('postcss-comment');
const postcssGlobalData = require('@csstools/postcss-global-data');

const path = require("path");
const fs = require("fs");

const presetEnvBrowsers = [
  '> 1.1% in RU',
  'Android >= 4',
  'ChromeAndroid >= 35',
  'ExplorerMobile >= 11',
  'Firefox ESR',
  'iOS >= 7',
  'OperaMobile >= 37',
  'Samsung >=3',
  'last 2 versions',
];

const browsersListExists = () => fs.existsSync(path.join(process.cwd(), '.browserslistrc'));

module.exports = () => {
  const presetEnvOptions = {};

  if (!browsersListExists()) {
    presetEnvOptions.browsers = presetEnvBrowsers;
  }

  return {
    parser: postcssComment,
    plugins: [
      postcssImport(),
      postcssGlobalData({
        files: [path.join(__dirname, 'src/public/assets/css/customMedia/customMedia.css')]
      }),
      postcssCustomMedia(),
      presetEnv(presetEnvOptions),
      postcssMixins({
        mixinsDir: path.join(__dirname, 'src/public/assets/css/mixins'),
      }),
      postcssNested(),
    ],
  };
};
