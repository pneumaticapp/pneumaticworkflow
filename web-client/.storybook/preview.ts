import type { Preview } from '@storybook/react';
import { reactIntl } from './reactIntl';

import '../src/public/assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../src/public/assets/fonts/iconsmind-s/css/iconsminds.css';
import '../src/public/assets/css/vendor/bootstrap.min.css';
import '../src/public/assets/css/sass/themes/gogo.light.yellow.scss';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'rc-switch/assets/index.css';
import 'react-phone-number-input/style.css';

const preview: Preview = {
  globals: {
    locale: reactIntl.defaultLocale,
    locales: {
        en_US: 'English',
        ru_RU: 'Russian',
    },
  },
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    reactIntl,
  },
};

export default preview;
