import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import postcssGlobalData from '@csstools/postcss-global-data';
import postcssComment from 'postcss-comment';
import postcssCustomMedia from 'postcss-custom-media';
import postcssImport from 'postcss-import';
import postcssMixins from 'postcss-mixins';
import postcssNested from 'postcss-nested';
import presetEnv from 'postcss-preset-env';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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

export default () => {
  const presetEnvOptions = {
    features: {
      // Handled by postcss-custom-media + postcss-nested in this pipeline.
      'custom-media-queries': false,
      'nesting-rules': false,
    },
  };

  if (!browsersListExists()) {
    presetEnvOptions.browsers = presetEnvBrowsers;
  }

  return {
    parser: postcssComment,
    plugins: [
      postcssImport(),
      postcssGlobalData({
        files: [path.join(__dirname, 'src/public/assets/css/customMedia/customMedia.css')],
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
