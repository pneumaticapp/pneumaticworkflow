import { ComponentType } from 'react';
import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  setWorkflowsFilterStatus,
  loadWorkflowsFilterTemplates,
  setWorkflowsFilterTemplate,
  changeWorkflowsSorting,
  setWorkflowsFilterPerfomers,
  setWorkflowsFilterWorkflowStarters,
  applyWorkflowsFilters,
  loadWorkflowsFilterSteps,
  setWorkflowsFilterSteps,
  updateCurrentPerformersCounters,
  updateWorkflowStartersCounters,
  clearWorkflowsFilters,
  updateWorkflowsTemplateStepsCounters,
  setWorkflowsFilterPerfomersGroup,
} from '../../redux/workflows/actions';
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
        values: {
          statusFilter,
          templatesIdsFilter,
          stepsIdsFilter,
          performersIdsFilter,
          performersGroupIdsFilter,
          workflowStartersIdsFilter
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
