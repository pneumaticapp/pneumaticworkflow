import * as React from 'react';
import { useIntl } from 'react-intl';

import { Filter, Button } from '../../../UI';
import { EXTERNAL_USER, getUserFullName } from '../../../../utils/users';
import { EWorkflowsStatus } from '../../../../types/workflow';
import { TUserListItem, TUserType } from '../../../../types/user';
import { StepName } from '../../../StepName';
import { isArrayWithItems } from '../../../../utils/helpers';
import {
  canFilterByCurrentPerformer,
  canFilterByTemplateStep,
  getSortingsByStatus,
  getVerboseSortings,
} from '../../../../utils/workflows/filters';
import { IWorkflowsFiltersProps } from '../../types';
import { AvatarWithGroup } from '../../../UI/AvatarWithGroup';
import { ETemplateOwnerType } from '../../../../types/template';

import styles from '../WorkflowsGridPage.css';

type TOptionUser = Pick<TUserListItem, 'id' | 'firstName' | 'lastName' | 'status' | 'email' | 'photo'> & {
  type?: TUserType;
};

type TOptionTemplate = {
  id: number;
  name: string;
  subOptions?: {
    id: number;
    apiName: string;
    name: React.ReactNode;
    number: number;
    count?: number;
  }[];
  areSubOptionsLoading?: boolean;
};

type TOptionTemplateStep = {
  id: number;
  apiName: string;
  number: number;
  name: string | React.ReactNode;
};

// @deprecated
export function WorkflowsFilters({
  sorting,
  areFiltersChanged,
  statusFilter,
  templatesIdsFilter,
  performersIdsFilter,
  performersGroupIdsFilter,
  workflowStartersIdsFilter,
  filterTemplates,
  users,
  groups,
  areUsersLoading = false,
  areFilterTemplatesLoading = false,
  tasksApiNamesFilter,
  performersCounters,
  workflowStartersCounters,
  clearFilters,
  setTasksFilter,
  loadTemplateSteps,
  setTemplatesFilter,
  setPerformersFilter,
  setPerformersGroupFilter,
  changeWorkflowsSorting,
  setStatusFilter,
  setWorkflowStartersFilter,
  updateWorkflowsTemplateStepsCounters,
}: IWorkflowsFiltersProps) {
  const { formatMessage } = useIntl();
  const { useState, useEffect } = React;

  // store tasks apiNames in state to handle async setting
  const [tasksApiNamesFilterState, setTasksApiNamesFilterState] = useState(tasksApiNamesFilter);

  useEffect(() => {
    setTasksFilter(tasksApiNamesFilterState);
  }, [tasksApiNamesFilterState]);

  const onChangeSetting =
    <T extends unknown>(handleChange: (value: T) => void) =>
      (value: T) => {
        handleChange(value);
      };

  const statusOptions = React.useMemo(
    () => [
      { id: EWorkflowsStatus.All, name: formatMessage({ id: 'sorting.workflows-all-statuses' }) },
      { id: EWorkflowsStatus.Running, name: formatMessage({ id: 'sorting.workflows-in-progress' }) },
      { id: EWorkflowsStatus.Snoozed, name: formatMessage({ id: 'sorting.workflows-snoozed' }) },
      { id: EWorkflowsStatus.Completed, name: formatMessage({ id: 'sorting.workflows-completed' }) },
    ],
    [],
  );

  const sortingOptions = React.useMemo(() => {
    return getVerboseSortings(getSortingsByStatus(statusFilter), formatMessage);
  }, [statusFilter]);

  const performersOptions = React.useMemo(
    () =>
      users.map((user) => ({
        ...user,
        count: performersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0,
      })),
    [users, performersCounters],
  );

  const performersGroupOptions = React.useMemo(
    () =>
      groups.map((user) => ({
        ...user,
        type: ETemplateOwnerType.UserGroup,
        firstName: user.name,
      })),
    [groups],
  ) as unknown as typeof performersOptions;

  const workflowStartersOptions = React.useMemo(() => {
    const normalizedUsers = users.map((user) => ({
      ...user,
      count: workflowStartersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0,
    }));

    return [
      {
        ...EXTERNAL_USER,
        count: workflowStartersCounters.find(({ sourceId }) => sourceId === -1)?.workflowsCount || 0,
      },
      ...normalizedUsers,
    ];
  }, [users, workflowStartersCounters]);

  const onCheckTemplateOption = (checkedTemplate: TOptionTemplate, callback?: () => void) => {
    if (!canFilterByTemplateStep(statusFilter)) {
      return;
    }

    const handleCheckSteps = (templateSteps: TOptionTemplateStep[]) => {
      const checkedTemplateSteps = tasksApiNamesFilterState.filter((checkedTaskApiName) => {
        return templateSteps.some((templateStep) => templateStep.apiName === checkedTaskApiName);
      });

      if (isArrayWithItems(checkedTemplateSteps)) {
        return;
      }

      const newSubOptionsIds = templateSteps.map(({ apiName }) => apiName);
      setTasksApiNamesFilterState((prevFilters) => [...prevFilters, ...newSubOptionsIds]);
    };

    loadTemplateSteps({
      templateId: checkedTemplate.id,
      onAfterLoaded: (steps) => {
        handleCheckSteps(steps);
        updateWorkflowsTemplateStepsCounters();
        callback?.();
      },
    });
  };

  const onUncheckTemplateOption = (uncheckedTemplate: TOptionTemplate) => {
    const { subOptions } = uncheckedTemplate;
    if (!subOptions) {
      return;
    }

    setTasksApiNamesFilterState((prevFilters) =>
      prevFilters.filter((taskApiName) => !subOptions.some((so) => so.apiName === taskApiName)),
    );
  };

  const onCheckTemplateStepOption = (templateId: number, taskApiName: string) => {
    if (!templatesIdsFilter.includes(templateId)) {
      setTemplatesFilter([...templatesIdsFilter, templateId]);
    }

    setTasksApiNamesFilterState((prevFilters) => [...prevFilters, taskApiName]);
  };

  const onUncheckTemplateStepOption = (templateId: number, taskApiName: string) => {
    setTasksApiNamesFilterState((prevFilters) => prevFilters.filter((s) => s !== taskApiName));
  };

  const onExpandTemplateOption = (checkedTemplate: TOptionTemplate) => {
    if (!canFilterByTemplateStep(statusFilter)) {
      return;
    }

    loadTemplateSteps({
      templateId: checkedTemplate.id,
      onAfterLoaded: updateWorkflowsTemplateStepsCounters,
    });
  };

  const templatesOptions = React.useMemo(() => {
    return filterTemplates.map(({ id, name, steps, areStepsLoading }) => {
      const option: TOptionTemplate = {
        id,
        name,
        ...(canFilterByTemplateStep(statusFilter) && {
          subOptions: steps
            .map((step) => ({
              ...step,
              name: <StepName initialStepName={step.name} templateId={id} />,
            }))
            .filter((step) => {
              return step.count;
            }),
          areSubOptionsLoading: areStepsLoading,
        }),
      };

      return option;
    });
  }, [filterTemplates, statusFilter]);

  const renderUserOption = (user: TOptionUser) => {
    return (
      <div className={styles['user-filter-option']}>
        <AvatarWithGroup size="sm" user={user} containerClassName={styles['user-filter-option_avatar']} />
        <span className={styles['user-filter-option_title']}>{getUserFullName(user)}</span>
      </div>
    );
  };

  return (
    <>
      <Filter
        key="status-filter"
        title={formatMessage({ id: 'workflows.filter-status' })}
        options={statusOptions}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={(status: EWorkflowsStatus) => {
          onChangeSetting(setStatusFilter)(status);
        }}
        selectedOption={statusFilter}
        containerClassName={styles['filter']}
        isInitiallyExpanded
      />
      <Filter
        key="templates-filter"
        title={formatMessage({ id: 'workflows.filter-template' })}
        options={templatesOptions}
        optionsTitle={formatMessage({ id: 'workflows.filter-template-options' })}
        isLoading={areFilterTemplatesLoading}
        optionIdKey="id"
        optionApiNameKey="apiName"
        optionLabelKey="name"
        changeFilter={(templates: number[]) => onChangeSetting(setTemplatesFilter)(templates)}
        isMultiple
        selectedOptions={templatesIdsFilter}
        selectedSubOptions={tasksApiNamesFilterState}
        containerClassName={styles['filter']}
        onCheckOption={onCheckTemplateOption}
        onUncheckOption={onUncheckTemplateOption}
        onCheckSubOption={onCheckTemplateStepOption}
        onUncheckSubOption={onUncheckTemplateStepOption}
        onExpandOption={onExpandTemplateOption}
      />
      {canFilterByCurrentPerformer(statusFilter) && (
        <Filter
          key="performers-filter"
          title={formatMessage({ id: 'workflows.filter-performer' })}
          options={[...performersGroupOptions, ...performersOptions]}
          optionsTitle={formatMessage({ id: 'workflows.filter-users-options' })}
          isLoading={areUsersLoading}
          optionIdKey="id"
          optionLabelKey="firstName"
          changeFilter={(_, seletedPerformers) => {
            const performers = seletedPerformers
              .filter((item: any) => item.type === ETemplateOwnerType.User)
              .map((lItem: any) => lItem.id);
            const selectedGroups = seletedPerformers
              .filter((item: any) => item.type === ETemplateOwnerType.UserGroup)
              .map((lItem: any) => lItem.id);

            onChangeSetting(setPerformersFilter)(performers);
            onChangeSetting(setPerformersGroupFilter)(selectedGroups);
          }}
          isMultiple
          selectedOptions={[...performersIdsFilter, ...performersGroupIdsFilter]}
          containerClassName={styles['filter']}
          renderOptionTitle={renderUserOption}
        />
      )}
      <Filter
        key="starter-filter"
        title={formatMessage({ id: 'workflows.filter-workflow-starter' })}
        options={workflowStartersOptions}
        optionsTitle={formatMessage({ id: 'workflows.filter-users-options' })}
        isLoading={areUsersLoading}
        optionIdKey="id"
        optionLabelKey="firstName"
        changeFilter={(workflowStarters: number[]) => onChangeSetting(setWorkflowStartersFilter)(workflowStarters)}
        isMultiple
        selectedOptions={workflowStartersIdsFilter}
        containerClassName={styles['filter']}
        renderOptionTitle={renderUserOption}
      />
      <Filter
        key="sorting-filter"
        title={formatMessage({ id: 'workflows.sorting' })}
        options={sortingOptions}
        optionIdKey="id"
        optionLabelKey="name"
        changeFilter={changeWorkflowsSorting}
        selectedOption={sorting}
        containerClassName={styles['filter']}
      />
      {areFiltersChanged && (
        <div className={styles['filter-buttons']}>
          <Button
            type="button"
            onClick={clearFilters}
            label={formatMessage({ id: 'workflows.clear-grid-filters' })}
            size="md"
          />
        </div>
      )}
    </>
  );
}
