import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';

import { IApplicationState } from '../../types/redux';
import {
  loadTemplate,
  loadTemplateFromSystem,
  setTemplate,
  resetTemplateStore,
  saveTemplate,
  setTemplateStatus,
  loadTemplateVariablesSuccess,
} from '../../redux/actions';
import { getNotDeletedUsers } from '../../utils/users';
import { getIsUserSubsribed } from '../../redux/selectors/user';

import { ITemplateEditProps, TemplateEdit } from './TemplateEdit';

type TWorkflowStoreProps = Pick<
  ITemplateEditProps,
  'authUser' | 'users' | 'template' | 'aiTemplate' | 'templateStatus' | 'isSubscribed'
>;

type TWorkflowDispatchProps = Pick<
  ITemplateEditProps,
  | 'loadTemplate'
  | 'loadTemplateFromSystem'
  | 'saveTemplate'
  | 'setTemplate'
  | 'resetTemplateStore'
  | 'setTemplateStatus'
  | 'loadTemplateVariablesSuccess'
>;

export function mapStateToProps(state: IApplicationState): TWorkflowStoreProps {
  const {
    accounts: { users },
    authUser,
    template: { data: workflow, status: workflowStatus, AITemplate },
  } = state;

  return {
    authUser,
    isSubscribed: getIsUserSubsribed(state),
    templateStatus: workflowStatus,
    template: workflow,
    aiTemplate: AITemplate.generatedData,
    users: getNotDeletedUsers(users),
  };
}

export const mapDispatchToProps: TWorkflowDispatchProps = {
  loadTemplate,
  loadTemplateFromSystem,
  resetTemplateStore,
  saveTemplate,
  setTemplate,
  setTemplateStatus,
  loadTemplateVariablesSuccess,
};

export const TemplateEditContainer = withRouter(
  connect<TWorkflowStoreProps, TWorkflowDispatchProps>(mapStateToProps, mapDispatchToProps)(TemplateEdit),
);
