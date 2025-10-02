import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import { history } from './utils/history';
import { getBrowserConfig } from './utils/getConfig';
import { store, persistor } from './redux/store';
import { initSentry } from './utils/initSentry';
import { AppContainer } from './components/App';
import { ErrorBoundary } from 'react-error-boundary';

import { ErrorFallback } from './components/ErrorFallback';

import { PersistGate } from 'redux-persist/integration/react';

/* polyfills */
import 'promise-polyfill/src/polyfill';
import 'whatwg-fetch';
import * as smoothscroll from 'smoothscroll-polyfill';
import { resetSuperuserToken } from './redux/auth/utils/superuserToken';

// Fix smooth scroll in Safari
smoothscroll.polyfill();

initSentry(getBrowserConfig);
addEventListener('beforeunload', resetSuperuserToken);

ReactDOM.render(
  <Provider store={store}>
    <React.Suspense fallback={<div className="loading" />}>
      <Router history={history}>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <PersistGate loading={null} persistor={persistor}>
            <AppContainer />
          </PersistGate>
        </ErrorBoundary>
      </Router>
    </React.Suspense>
  </Provider>,
  document.getElementById('pneumatic-frontend'),
);
