import { RootStateOrAny } from 'react-redux';
import { combineReducers } from 'redux';

import { IApplicationState } from '../types/redux';

import { general } from './general';
import { accounts } from './accounts';
import { authUser } from './auth';
import { dashboard } from './dashboard';
import { genericTemplates } from './genericTemplates';
import { initialState } from './store';
import { teamInvites } from './team';
import { menu } from './menu';
import { notifications } from './notifications';
import { workflows } from './workflows';
import { profile } from './profile';
import { settings } from './settings';
import { task } from './task';
import { highlights } from './highlights';
import { templates } from './templates';
import { selectTemplateModal } from './selectTemplateModal';
import { template } from './template';
import { integrations } from './integrations';
import { runWorkflowModal } from './runWorkflowModal';
import { tasks } from './tasks';
import { webhooks } from './webhooks';
import { tenants } from './tenants';
import { pages } from './pages';
import { EAuthActions } from './actions';

export const reducers = combineReducers({
  general,
  accounts,
  genericTemplates,
  authUser,
  dashboard,
  menu,
  notifications,
  workflows,
  profile,
  settings,
  teamInvites,
  task,
  tasks,
  highlights,
  templates,
  selectTemplateModal,
  template,
  integrations,
  runWorkflowModal,
  webhooks,
  tenants,
  pages,
});

// eslint-disable-next-line @typescript-eslint/default-param-last
export const rootReducer: RootStateOrAny = (state: IApplicationState = initialState, action: any) => {
  if (action.type === EAuthActions.LogoutUserSuccess) {
    return reducers(initialState, action);
  }

  return reducers(state, action);
};
