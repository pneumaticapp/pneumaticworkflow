import { connect } from 'react-redux';
import { compose } from 'redux';

import { IWorkflowsLayoutComponentProps, WorkflowsLayoutComponent } from './WorkflowsLayout';
import { IApplicationState } from '../../types/redux';
import {
  TWorkflowsFiltersStoreProps,
  createWorkflowsFiltersContainer,
} from '../../components/Workflows/createWorkflowsFiltersContainer';
import { removeWorkflowFromList, setWorkflowsView, setWorkflowsFilterSelectedFields } from '../../redux/actions';
import {
  closeWorkflowLogPopup,
  changeWorkflowsSorting,
  setFilterStatus as setWorkflowsFilterStatus,
  setFilterTemplate as setWorkflowsFilterTemplate,
  setFilterTemplateSteps as setWorkflowsFilterSteps,
  setFilterPerformers as setWorkflowsFilterPerfomers,
  setFilterPerformersGroup as setWorkflowsFilterPerfomersGroup,
  setFilterWorkflowStarters as setWorkflowsFilterWorkflowStarters,
  clearFilters as clearWorkflowsFilters,
} from '../../redux/workflows/slice';

import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { EWorkflowsSorting, EWorkflowsStatus, EWorkflowsView } from '../../types/workflow';

type TStoreProps = Pick<IWorkflowsLayoutComponentProps, 'workflowId' | 'workflowsView'>;
type TDispatchProps = Pick<
  IWorkflowsLayoutComponentProps,
  'closeWorkflowLogPopup' | 'removeWorkflowFromList' | 'setWorkflowsView'
>;

const mapStateToProps = ({
  workflows: {
    workflow,
    workflowsSettings: { view },
  },
}: IApplicationState): TStoreProps => {
  return {
    workflowId: workflow?.id || null,
    workflowsView: view,
  };
};

const mapDispatchToProps: TDispatchProps = {
  closeWorkflowLogPopup,
  removeWorkflowFromList,
  setWorkflowsView,
};

const SyncedWorkflowsFilters = withSyncedQueryString<TWorkflowsFiltersStoreProps>(
  [
    {
      propName: 'view',
      queryParamName: 'view',
      defaultAction: setWorkflowsView(EWorkflowsView.Table),
      createAction: setWorkflowsView,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'statusFilter',
      queryParamName: 'type',
      defaultAction: setWorkflowsFilterStatus(EWorkflowsStatus.Running),
      createAction: setWorkflowsFilterStatus,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'templatesIdsFilter',
      queryParamName: 'templates',
      defaultAction: setWorkflowsFilterTemplate([]),
      createAction: (queryParam) => {
        const templates = queryParam.split(',').map(Number);
        if (templates.every(Number.isInteger)) {
          return setWorkflowsFilterTemplate(templates);
        }

        return setWorkflowsFilterTemplate([]);
      },
      getQueryParamByProp: (value: number[]) => value.join(','),
    },
    {
      propName: 'stepsIdsFilter',
      queryParamName: 'steps',
      defaultAction: setWorkflowsFilterSteps([]),
      createAction: (queryParam) => {
        const steps = queryParam.split(',').map(Number);
        if (steps.every(Number.isInteger)) {
          return setWorkflowsFilterSteps(steps);
        }

        return setWorkflowsFilterSteps([]);
      },
      getQueryParamByProp: (value: number[]) => value.join(','),
    },
    {
      propName: 'performersIdsFilter',
      queryParamName: 'performers',
      defaultAction: setWorkflowsFilterPerfomers([]),
      createAction: (queryParam) => {
        const performers = queryParam.split(',').map(Number);
        if (performers.every(Number.isInteger)) {
          return setWorkflowsFilterPerfomers(performers);
        }

        return setWorkflowsFilterPerfomers([]);
      },
      getQueryParamByProp: (value: number[]) => value.join(','),
    },
    {
      propName: 'performersGroupIdsFilter',
      queryParamName: 'groups',
      defaultAction: setWorkflowsFilterPerfomersGroup([]),
      createAction: (queryParam) => {
        const performers = queryParam.split(',').map(Number);
        if (performers.every(Number.isInteger)) {
          return setWorkflowsFilterPerfomersGroup(performers);
        }

        return setWorkflowsFilterPerfomersGroup([]);
      },
      getQueryParamByProp: (value: number[]) => value.join(','),
    },
    {
      propName: 'workflowStartersIdsFilter',
      queryParamName: 'workflow_starters',
      defaultAction: setWorkflowsFilterWorkflowStarters([]),
      createAction: (queryParam) => {
        const workflowStarters = queryParam.split(',').map(Number);
        if (workflowStarters.every(Number.isInteger)) {
          return setWorkflowsFilterWorkflowStarters(workflowStarters);
        }

        return setWorkflowsFilterWorkflowStarters([]);
      },
      getQueryParamByProp: (value: number[]) => value.join(','),
    },
    {
      propName: 'sorting',
      queryParamName: 'sorting',
      defaultAction: changeWorkflowsSorting(EWorkflowsSorting.DateDesc),
      createAction: changeWorkflowsSorting,
      getQueryParamByProp: (value) => value,
    },
    {
      propName: 'selectedFields',
      queryParamName: 'fields',
      defaultAction: setWorkflowsFilterSelectedFields([]),
      createAction: (queryParam) => setWorkflowsFilterSelectedFields(queryParam.split(',')),
      getQueryParamByProp: (value: string[]) => value.join(','),
    },
  ],
  clearWorkflowsFilters(),
)(WorkflowsLayoutComponent);

export const WorkflowsLayoutContainer = compose(
  connect(mapStateToProps, mapDispatchToProps),
  createWorkflowsFiltersContainer,
)(SyncedWorkflowsFilters);
