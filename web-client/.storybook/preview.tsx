import './initData';
import React from 'react';
import type { Preview } from '@storybook/react';
import { reactIntl } from './reactIntl';
import { Provider } from 'react-redux';
import { store } from '../src/public/redux/store';
import { BrowserRouter } from 'react-router-dom';

import '../src/public/assets/css/vendor/bootstrap.min.css';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'react-phone-number-input/style.css';
import 'rc-switch/assets/index.css';
import '../src/public/assets/fonts/iconsmind-s/css/iconsminds.css';
import '../src/public/assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../src/public/assets/css/sass/themes/gogo.light.yellow.scss';
import '../src/public/assets/css/style.css';

const preview: Preview = {
  decorators: [
    (Story, args) => {
      return (
        <Provider store={store}>
          <BrowserRouter>
            <Story />
          </BrowserRouter>
        </Provider>
      );
    },
  ],
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
