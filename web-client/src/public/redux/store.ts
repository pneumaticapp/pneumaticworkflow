import { createStore, applyMiddleware, compose } from 'redux';
import { RootStateOrAny } from 'react-redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import createSagaMiddleware from 'redux-saga';
import { persistStore, persistReducer, PersistConfig } from 'redux-persist';
import localStorage from 'redux-persist/lib/storage';
import merge from 'lodash.merge';
import { createFilter } from 'redux-persist-transform-filter';

import { IApplicationState } from '../types/redux';
import { isClient } from '../utils/helpers';
import { createDeclineForbiddenActionsMiddleware } from './utils/createDeclineForbiddenActionsMiddleware';

import { rootReducer } from './reducers';
import { rootSaga as sagas } from './sagas';

const sagaMiddleware = createSagaMiddleware();
const declineForbiddenActionsMiddleware = createDeclineForbiddenActionsMiddleware();

const middlewares = [declineForbiddenActionsMiddleware, sagaMiddleware];

export const initialState = {} as IApplicationState;

export function configureStore(state: IApplicationState = initialState) {
  const saveDashboardModeFilter = createFilter<IApplicationState, {}>('dashboard', ['mode']);
  const saveTasksSortingFilter = createFilter<IApplicationState, {}>('tasks', ['tasksSettings.sorting']);

  const persistConfig: PersistConfig<IApplicationState> = {
    key: 'primary',
    storage: localStorage,
    transforms: [saveDashboardModeFilter, saveTasksSortingFilter],
    whitelist: ['dashboard', 'tasks'],
    stateReconciler: (inbound, original) => {
      const reconcilationResult = merge(original, inbound);

      return reconcilationResult;
    },
  };

  const persistedReducer = persistReducer(persistConfig, rootReducer);
  const composeEnhancers =
    (isClient() &&
      composeWithDevTools({
        trace: true,
        traceLimit: 25,
      })) ||
    compose;
  const store = createStore(
    persistedReducer,
    state as RootStateOrAny,
    composeEnhancers(applyMiddleware(...middlewares)),
  );
  const persistor = persistStore(store);

  sagaMiddleware.run(sagas);

  return { store, persistor };
}

export const { store, persistor } = configureStore();
