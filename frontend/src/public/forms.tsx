import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Redirect, Route, Router, Switch } from 'react-router-dom';
import { IntlProvider } from 'react-intl';
import { Provider } from 'react-redux';

import { createBrowserHistory } from 'history';
import { store } from './redux/store';

import { initSentry } from './utils/initSentry';
import { getPublicFormConfig } from './utils/getConfig';

import { getFormsBasename } from './utils/identifyAppPart/constants';
import { EPublicFormRoutes } from './constants/routes';
import { BRAND } from './constants/branding';
import { SharedPublicForm, EmbeddedPublicForm } from './components/PublicFormsApp';
import { AppLocale } from './lang';
import { applyDocumentLocale } from './lang/document';

/* polyfills */
import 'promise-polyfill/src/polyfill';
import './assets/css/style.css';

initSentry(getPublicFormConfig, 'forms');

const formsHistory = createBrowserHistory({
  basename: getFormsBasename(window.location.pathname) || '/',
});
const formsLocale = store.getState().settings.locale;
const currentAppLocale = AppLocale[formsLocale];
applyDocumentLocale(formsLocale);

ReactDOM.render(
  <Provider store={store}>
    <React.Suspense fallback={<div className="loading" />}>
      <Router history={formsHistory}>
        <IntlProvider locale={currentAppLocale.locale} messages={currentAppLocale.messages}>
          <Switch>
            <Route
              path={EPublicFormRoutes.Error}
              component={() => {
                window.location.href = BRAND.homePath;
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
