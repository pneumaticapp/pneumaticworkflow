import { ComponentType, createElement } from 'react';
import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import { IWorkflowsProps } from './types';
import { openSelectTemplateModal, openRunWorkflowModal } from '../../redux/actions';
import {
  openWorkflowLogPopup,
  changeWorkflowsSearchText,
  loadWorkflowsList as loadWorkflowsListAction,
  loadFilterTemplates as loadWorkflowsFilterTemplates,
  setFilterTemplateSteps as setWorkflowsFilterSteps,
  resetWorkflows,
  removeWorkflowFromList,
} from '../../redux/workflows/slice';

type TStoreProps = Pick<
  IWorkflowsProps,
  'workflowsLoadingStatus' | 'workflowsList' | 'templatesFilter' | 'searchText' | 'stepsIdsFilter' | 'view'
>;

type TDispatchProps = Pick<
  IWorkflowsProps,
  | 'loadWorkflowsList'
  | 'openWorkflowLogPopup'
  | 'loadTemplatesTitles'
  | 'resetWorkflows'
  | 'openSelectTemplateModal'
  | 'openRunWorkflowModal'
  | 'onSearch'
  | 'setStepsFilter'
  | 'removeWorkflowFromList'
>;

export function mapStateToProps({
  workflows: {
    workflowsSearchText,
    workflowsLoadingStatus,
    workflowsList,
    workflowsSettings: {
      view,
      values: { templatesIdsFilter, stepsIdsFilter },
      templateList,
    },
  },
}: IApplicationState): TStoreProps {
  const templatesFilter = templateList.items.filter((template) =>
    templatesIdsFilter.some((templateId) => templateId === template.id),
  );

  return {
    workflowsLoadingStatus,
    workflowsList,
    templatesFilter,
    stepsIdsFilter,
    searchText: workflowsSearchText,
    view,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  loadWorkflowsList: loadWorkflowsListAction,
  openWorkflowLogPopup,
  loadTemplatesTitles: loadWorkflowsFilterTemplates,
  resetWorkflows,
  setStepsFilter: setWorkflowsFilterSteps,
  openSelectTemplateModal,
  openRunWorkflowModal,
  onSearch: changeWorkflowsSearchText,
  removeWorkflowFromList,
};

export const createWorkflowsContainer = (Component: ComponentType<IWorkflowsProps>) => {
  const WorkflowsContainer = ({ loadWorkflowsList, loadTemplatesTitles, ...restProps }: IWorkflowsProps) => {
    return createElement(Component, { loadWorkflowsList, loadTemplatesTitles, ...restProps });
  };

  return connect<TStoreProps, TDispatchProps>(mapStateToProps, mapDispatchToProps)(WorkflowsContainer);
};
