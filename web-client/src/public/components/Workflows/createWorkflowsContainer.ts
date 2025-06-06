import { ComponentType, useEffect, createElement } from 'react';
import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import { IWorkflowsProps } from './types';
import {
  loadWorkflowsList as loadWorkflowsListAction,
  openWorkflowLogPopup,
  loadWorkflowsFilterTemplates,
  resetWorkflows,
  openSelectTemplateModal,
  openRunWorkflowModal,
  changeWorkflowsSearchText,
  removeWorkflowFromList,
  setWorkflowsFilterSteps,
} from '../../redux/actions';

type TStoreProps = Pick<
  IWorkflowsProps,
  'workflowsLoadingStatus' |
  'workflowsList' |
  'templatesFilter' |
  'searchText' |
  'stepsIdsFilter' |
  'view'
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
      values: {
        templatesIdsFilter,
        stepsIdsFilter
      },
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
    useEffect(() => {
      loadTemplatesTitles();
    }, [loadWorkflowsList, loadTemplatesTitles]);

    return createElement(Component, { loadWorkflowsList, loadTemplatesTitles, ...restProps });
  };

  return connect<TStoreProps, TDispatchProps>(mapStateToProps, mapDispatchToProps)(WorkflowsContainer);
};
