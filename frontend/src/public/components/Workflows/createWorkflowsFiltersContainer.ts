import { ComponentType } from 'react';
import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  changeWorkflowsSorting,
  loadFilterTemplates as loadWorkflowsFilterTemplates,
  loadFilterSteps as loadWorkflowsFilterSteps,
  setFilterStatus as setWorkflowsFilterStatus,
  setFilterTemplate as setWorkflowsFilterTemplate,
  setFilterTemplateSteps as setWorkflowsFilterSteps,
  setFilterPerformers as setWorkflowsFilterPerfomers,
  setFilterPerformersGroup as setWorkflowsFilterPerfomersGroup,
  setFilterWorkflowStarters as setWorkflowsFilterWorkflowStarters,
  clearFilters as clearWorkflowsFilters,
  applyFilters as applyWorkflowsFilters,
  updateCurrentPerformersCounters,
  updateWorkflowStartersCounters,
  updateWorkflowsTemplateStepsCounters,
} from '../../redux/workflows/slice';
import { getActiveUsers } from '../../utils/users';
import { getIsUserSubsribed } from '../../redux/selectors/user';
import { IWorkflowsFiltersProps } from './types';

export type TWorkflowsFiltersStoreProps = Pick<
  IWorkflowsFiltersProps,
  | 'sorting'
  | 'areFiltersChanged'
  | 'statusFilter'
  | 'templatesIdsFilter'
  | 'stepsIdsFilter'
  | 'performersIdsFilter'
  | 'performersGroupIdsFilter'
  | 'filterTemplates'
  | 'areFilterTemplatesLoading'
  | 'workflowStartersIdsFilter'
  | 'users'
  | 'groups'
  | 'areUsersLoading'
  | 'isSubscribed'
  | 'performersCounters'
  | 'workflowStartersCounters'
  | 'view'
  | 'selectedFields'
>;

type TDispatchProps = Pick<
  IWorkflowsFiltersProps,
  | 'loadTemplatesTitles'
  | 'setTemplatesFilter'
  | 'setPerformersFilter'
  | 'setPerformersGroupFilter'
  | 'changeWorkflowsSorting'
  | 'setStatusFilter'
  | 'applyFilters'
  | 'setWorkflowStartersFilter'
  | 'loadTemplateSteps'
  | 'setStepsFilter'
  | 'updateCurrentPerformersCounters'
  | 'updateWorkflowStartersCounters'
  | 'updateWorkflowsTemplateStepsCounters'
  | 'clearFilters'
>;

export function mapStateToProps(state: IApplicationState): TWorkflowsFiltersStoreProps {
  const {
    workflows: {
      workflowsSettings: {
        view,
        templateList,
        sorting,
        areFiltersChanged,
        selectedFields,
        values: {
          statusFilter,
          templatesIdsFilter,
          stepsIdsFilter,
          performersIdsFilter,
          performersGroupIdsFilter,
          workflowStartersIdsFilter,
        },
        counters: { performersCounters, workflowStartersCounters },
      },
    },
    groups,
    accounts: { users, isLoading: areUsersLoading },
  } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    sorting,
    areFiltersChanged,
    statusFilter,
    templatesIdsFilter,
    stepsIdsFilter,
    filterTemplates: templateList.items,
    performersIdsFilter,
    performersGroupIdsFilter,
    workflowStartersIdsFilter,
    groups: groups.list,
    users: getActiveUsers(users),
    areFilterTemplatesLoading: templateList.isLoading,
    areUsersLoading,
    isSubscribed,
    performersCounters,
    workflowStartersCounters,
    view,
    selectedFields,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  loadTemplatesTitles: loadWorkflowsFilterTemplates,
  changeWorkflowsSorting,
  setStatusFilter: setWorkflowsFilterStatus,
  setTemplatesFilter: setWorkflowsFilterTemplate,
  setPerformersFilter: setWorkflowsFilterPerfomers,
  setPerformersGroupFilter: setWorkflowsFilterPerfomersGroup,
  applyFilters: applyWorkflowsFilters,
  setWorkflowStartersFilter: setWorkflowsFilterWorkflowStarters,
  loadTemplateSteps: loadWorkflowsFilterSteps,
  setStepsFilter: setWorkflowsFilterSteps,
  updateCurrentPerformersCounters,
  updateWorkflowStartersCounters,
  updateWorkflowsTemplateStepsCounters,
  clearFilters: clearWorkflowsFilters,
};

export const createWorkflowsFiltersContainer = <T extends IWorkflowsFiltersProps>(component: ComponentType<T>) => {
  // @ts-ignore
  return connect(mapStateToProps, mapDispatchToProps)(component);
};
