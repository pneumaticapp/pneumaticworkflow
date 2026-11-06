import { combineReducers } from 'redux';
import type { AnyAction } from 'redux';

import { general } from './general';
import { authUser } from './auth';
import { dashboard } from './dashboard';
import { genericTemplates } from './genericTemplates';
import { menu } from './menu';
import { notifications } from './notifications';
import { profile } from './profile';
import { settings } from './settings';
import { task } from './task';
import { highlights } from './highlights';
import { templates } from './templates';
import { selectTemplateModal } from './selectTemplateModal';
import { template } from './template';
import { integrations } from './integrations';
import { runWorkflowModal } from './runWorkflowModal';
import { webhooks } from './webhooks';
import { tenants } from './tenants';
import { EAuthActions } from './auth/actions';
import groups from './groups/slice';

import pages from './pages/slice';
import team from './team/slice';
import workflows from './workflows/slice';
import accounts from './accounts/slice';
import tasks from './tasks/slice';
import datasets from './datasets/slice';
import fieldsets from './fieldsets/slice';
import permissions from './permissions/slice';
import templateGraphView from './templateGraphView/slice';

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
  team,
  groups,
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
  datasets,
  fieldsets,
  permissions,
  templateGraphView,
  pages,
});

export const rootReducer = (state: ReturnType<typeof reducers> | undefined, action: AnyAction) => {
  if (action.type === EAuthActions.LogoutUserSuccess) {
    return reducers(undefined, action);
  }

  return reducers(state, action);
};
