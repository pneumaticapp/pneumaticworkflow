import { configureStore } from '@reduxjs/toolkit';
import createSagaMiddleware from 'redux-saga';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import type { PersistConfig } from 'redux-persist';
import localStorage from 'redux-persist/lib/storage';
import { createFilter } from 'redux-persist-transform-filter';
import type { IDashboardStore } from './dashboard/types';
import type { IStoreTasks } from './tasks/types';
import type { ITasksSettings } from '../types/tasks';
import { createDeclineForbiddenActionsMiddleware } from './utils/createDeclineForbiddenActionsMiddleware';
import { mergePersistedState } from './utils/mergePersistedState';
import { EHighlightsActions } from './highlights/actions';
import { reducers, rootReducer } from './reducers';
import { rootSaga as sagas } from './sagas';

const sagaMiddleware = createSagaMiddleware();
const declineForbiddenActionsMiddleware = createDeclineForbiddenActionsMiddleware();

const saveDashboardModeFilter = createFilter<IDashboardStore, Pick<IDashboardStore, 'mode'>>('dashboard', ['mode']);
const saveTasksSortingFilter = createFilter<IStoreTasks, { tasksSettings: Pick<ITasksSettings, 'sorting'> }>('tasks', [
  'tasksSettings.sorting',
]);

const persistConfig: PersistConfig<ReturnType<typeof reducers>> = {
  key: 'primary',
  storage: localStorage,
  transforms: [saveDashboardModeFilter, saveTasksSortingFilter],
  whitelist: ['dashboard', 'tasks'],
  stateReconciler: mergePersistedState,
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      thunk: false,
      serializableCheck: {
        ignoredActions: [
          FLUSH,
          REHYDRATE,
          PAUSE,
          PERSIST,
          PURGE,
          REGISTER,
          EHighlightsActions.SetStartDate,
          EHighlightsActions.SetEndDate,
        ],
        ignoredActionPaths: [
          /^payload\.on[A-Z]\w*$/,
          'payload.photo',
          'payload.startDate',
          'payload.endDate',
          'payload.eventDateFrom',
          'payload.eventDateTo',
          /^payload\.\d+(\.subs\.\d+)?\.iconComponent$/,
          /^payload\.variables\.\d+\.richSubtitle$/,
        ],
        ignoredPaths: [
          'highlights.filters.startDate',
          'highlights.filters.endDate',
          /^menu\.items\.\d+(\.subs\.\d+)?\.iconComponent$/,
          /^templates\.templatesVariablesMap\.\d+\.\d+\.richSubtitle$/,
        ],
      },
    }).concat(declineForbiddenActionsMiddleware, sagaMiddleware),
  devTools: {
    trace: true,
    traceLimit: 25,
  },
});

export const persistor = persistStore(store);

sagaMiddleware.run(sagas);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
