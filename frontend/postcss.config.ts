/// <reference types="node" />
import path from 'node:path';

import postcssGlobalData from '@csstools/postcss-global-data';
import postcssMixins from 'postcss-mixins';
import postcssNested from 'postcss-nested';
import presetEnv from 'postcss-preset-env';

const cssDir = path.resolve(__dirname, 'src/public/assets/css');
const customMediaFile = path.join(cssDir, 'customMedia/customMedia.css');
const mixinsDir = path.join(cssDir, 'mixins');

export default () => ({
  plugins: [
    postcssGlobalData({ files: [customMediaFile] }),
    postcssMixins({ mixinsDir }),
    postcssNested(),
    presetEnv({
      features: {
        'nesting-rules': false,
      },
    }),
  ],
});
