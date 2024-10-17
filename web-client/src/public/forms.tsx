import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Redirect, Route, Router, Switch } from 'react-router-dom';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';

import { store } from './redux/store';
import { history } from './utils/history';

import { initSentry } from './utils/initSentry';
import { getPublicFormConfig } from './utils/getConfig';

import { EPublicFormRoutes } from './constants/routes';
import { SharedPublicForm, EmbeddedPublicForm } from './components/PublicFormsApp';
import { AppLocale } from './lang';
import { defaultLocale } from './constants/defaultValues';

/* polyfills */
import 'promise-polyfill/src/polyfill';
import 'whatwg-fetch';
import './assets/css/style.css';

initSentry(getPublicFormConfig);

const {
  config: { mainPage },
} = getPublicFormConfig();
const currentAppLocale = AppLocale[defaultLocale];

ReactDOM.render(
  <Provider store={store}>
    <React.Suspense fallback={<div className="loading" />}>
      {/* Оборачивать приложение в BrowserRouter удобнее здесь, если понадобится добавлять SSR */}

      <Router history={history}>
        <IntlProvider locale={currentAppLocale.locale} messages={currentAppLocale.messages}>
          <Switch>
            <Route
              path={EPublicFormRoutes.Error}
              component={() => {
                window.location.href = mainPage;
                return null;
              }}
            />
            <Route exact path={EPublicFormRoutes.SharedForm} component={SharedPublicForm} />
            <Route exact path={EPublicFormRoutes.EmbeddedForm} component={EmbeddedPublicForm} />
            <Redirect to={EPublicFormRoutes.Error} />
          </Switch>
        </IntlProvider>
      </Router>
    </React.Suspense>
  </Provider>,
  document.getElementById('pneumatic-frontend'),
);
