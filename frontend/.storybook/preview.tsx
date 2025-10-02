import './initData';
import React from 'react';
import type { Preview } from '@storybook/react';
import { reactIntl } from './reactIntl';
import { Provider } from 'react-redux';
import { store } from '../src/public/redux/store';
import { BrowserRouter } from 'react-router-dom';
import { createStore, applyMiddleware } from 'redux';
import createSagaMiddleware from 'redux-saga';
import { IntlProvider } from 'react-intl';

import { rootReducer } from '../src/public/redux/reducers';
import { rootSaga } from '../src/public/redux/sagas';

import '../src/public/assets/css/vendor/bootstrap.min.css';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'react-phone-number-input/style.css';
import 'react-datepicker/dist/react-datepicker.css';
import '../src/public/assets/css/library/react-datepicker.css';
import 'rc-switch/assets/index.css';
import '../src/public/assets/fonts/iconsmind-s/css/iconsminds.css';
import '../src/public/assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../src/public/assets/css/sass/themes/gogo.light.yellow.scss';
import '../src/public/assets/css/style.css';



const preview: Preview = {
  decorators: [
    (Story, context) => {
      const sagaMiddleware = createSagaMiddleware();
      const customStore = context.parameters?.store
        ? createStore(
          rootReducer,
          { ...preview.parameters?.store, ...context.parameters.store },
          applyMiddleware(sagaMiddleware)
        )
        : store;

      if (context.parameters?.store) {
        sagaMiddleware.run(rootSaga);
      }
      // Получаем текущую локаль из глобальных параметров
      const locale = context.globals.locale || reactIntl.defaultLocale;
      
      return (
        <Provider store={customStore}>
          <BrowserRouter>
            <IntlProvider
              messages={reactIntl.messages[locale]}
              locale={locale}
              defaultLocale={reactIntl.defaultLocale}
            >
              <Story />
            </IntlProvider>
          </BrowserRouter>
        </Provider>
      );
    },
  ],
  globals: {
    locale: reactIntl.defaultLocale,
    locales: {
      en: 'English',
      ru: 'Russian',
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
    store: {}
  },
};

export default preview;