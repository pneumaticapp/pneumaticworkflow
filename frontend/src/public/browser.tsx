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

const root = document.getElementById('pneumatic-frontend');

const storeRef = { current: store };
const persistorRef = { current: persistor };
if (typeof window !== 'undefined' && !(window as Window & { __REDUX_STORE_REF__?: typeof storeRef }).__REDUX_STORE_REF__) {
  (window as Window & { __REDUX_STORE_REF__?: typeof storeRef; __REDUX_PERSISTOR_REF__?: typeof persistorRef }).__REDUX_STORE_REF__ = storeRef;
  (window as Window & { __REDUX_PERSISTOR_REF__?: typeof persistorRef }).__REDUX_PERSISTOR_REF__ = persistorRef;
}

function render(App: React.ComponentType) {
  const currentStore = (window as Window & { __REDUX_STORE_REF__?: { current: typeof store } }).__REDUX_STORE_REF__?.current ?? store;
  const currentPersistor = (window as Window & { __REDUX_PERSISTOR_REF__?: { current: typeof persistor } }).__REDUX_PERSISTOR_REF__?.current ?? persistor;
  ReactDOM.render(
    <Provider store={currentStore}>
      <React.Suspense fallback={<div className="loading" />}>
        <Router history={history}>
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <PersistGate loading={null} persistor={currentPersistor}>
              <App />
            </PersistGate>
          </ErrorBoundary>
        </Router>
      </React.Suspense>
    </Provider>,
    root,
  );
}

render(AppContainer);

const hot = (module as NodeModule & {
  hot?: {
    accept: (pathOrCallback: string | (() => void), callback?: () => void) => void;
  };
}).hot;
if (hot) {
  hot.accept('./components/App', () => {
    const { AppContainer: NextAppContainer } = require('./components/App');
    render(NextAppContainer);
  });
  hot.accept(() => {
    const { AppContainer: NextAppContainer } = require('./components/App');
    render(NextAppContainer);
  });
}
