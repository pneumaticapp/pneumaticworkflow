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
import { SharedPublicForm, EmbeddedPublicForm } from './components/PublicFormsApp';
import { AppLocale } from './lang';
import { defaultLocale } from './constants/defaultValues';

/* polyfills */
import 'promise-polyfill/src/polyfill';
import './assets/css/style.css';

initSentry(getPublicFormConfig, 'forms');

const {
  config: { mainPage },
} = getPublicFormConfig();

const formsHistory = createBrowserHistory({
  basename: getFormsBasename(window.location.pathname) || '/',
});
const currentAppLocale = AppLocale[defaultLocale];

ReactDOM.render(
  <Provider store={store}>
    <React.Suspense fallback={<div className="loading" />}>

      <Router history={formsHistory}>
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
