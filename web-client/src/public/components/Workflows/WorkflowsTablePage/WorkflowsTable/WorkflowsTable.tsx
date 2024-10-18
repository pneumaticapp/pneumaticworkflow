/* eslint-disable */
import React, { useCallback, useEffect, useState } from 'react';
import { useTable, Column, TableOptions } from 'react-table';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import { createPortal } from 'react-dom';
import { debounce } from 'throttle-debounce';

import { TableColumns } from './types';
import * as ColumnCells from './Columns/Cells';

import { WorkflowsPlaceholderIcon } from '../../WorkflowsPlaceholderIcon';
import { Avatar, FilterSelect, InputField, Loader, Placeholder } from '../../../UI';
import { IWorkflowsList } from '../../../../types/redux';
import { TOpenWorkflowLogPopupPayload, TRemoveWorkflowFromListPayload } from '../../../../redux/actions';
import { SearchMediumIcon } from '../../../icons';
import { EWorkflowsLoadingStatus, EWorkflowsStatus } from '../../../../types/workflow';
import { IWorkflowsFiltersProps } from '../../types';
import { isArrayWithItems } from '../../../../utils/helpers';
import { canFilterByTemplateStep } from '../../../../utils/workflows/filters';
import { StepName } from '../../../StepName';
import { EXTERNAL_USER, getUserFullName } from '../../../../utils/users';

import styles from './WorkflowsTable.css';

export interface IWorkflowsTableProps extends IWorkflowsFiltersProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  workflowsList: IWorkflowsList;
  searchText: string;
  onSearch(value: string): void;
  loadWorkflowsList(id: number): void;
  removeWorkflowFromList(payload: TRemoveWorkflowFromListPayload): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
}

export function WorkflowsTable({
  templatesIdsFilter,
  workflowsLoadingStatus,
  workflowsList,
  searchText,
  users,
  workflowStartersCounters,
  workflowStartersIdsFilter,
  stepsIdsFilter,
  filterTemplates,
  performersIdsFilter,
  performersCounters,
  statusFilter,
  setWorkflowStartersFilter,
  setStepsFilter,
  onSearch,
  loadWorkflowsList,
  removeWorkflowFromList,
  openWorkflowLogPopup,
  setPerformersFilter,
  applyFilters,
}: IWorkflowsTableProps) {
  const { formatMessage } = useIntl();

  const [searchQuery, setSearchQuery] = useState(searchText);

  const tableWrapperRef = React.useRef<HTMLDivElement | null>(null);
  const debounceOnSearch = useCallback(debounce(500, onSearch), []);

  useEffect(() => {
    debounceOnSearch(searchQuery);
  }, [searchQuery]);

  React.useEffect(()=>{
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && stepsIdsFilter.length) {
      setStepsFilter([]);
    }
  }, [workflowsLoadingStatus])

  const workflowStartersOptions = React.useMemo(() => {
    const usersWithExternal = [EXTERNAL_USER, ...users];

    const normalizedUsers = usersWithExternal.map((user) => {
      const userFullName = getUserFullName(user);

      return {
        ...user,
        displayName: (
          <div className={styles['user']}>
            <Avatar user={user} className={styles['user-avatar']} size="sm" />
            <span className={styles['user-name']}>{userFullName}</span>
          </div>
        ),
        count: workflowStartersCounters.find(({ userId }) => userId === user.id)?.workflowsCount || 0,
        searchByText: userFullName,
      };
    });

    return normalizedUsers;
  }, [users.length, workflowStartersCounters]);

  const performersOptions = React.useMemo(
    () =>
      users.map((user) => {
        const userFullName = getUserFullName(user);

        return {
          ...user,
          displayName: (
            <div className={styles['user']}>
              <Avatar user={user} size="sm" />
              <span className={styles['user-name']}>{userFullName}</span>
            </div>
          ),
          count: performersCounters.find(({ userId }) => userId === user.id)?.workflowsCount || 0,
          searchByText: userFullName,
        };
      }),
    [users.length, performersCounters],
  );

  const renderSearch = () => {
    return (
      <div className={styles['search']}>
        <SearchMediumIcon className={styles['search__icon']} />
        <InputField
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          className={styles['search-field__input']}
          placeholder={formatMessage({ id: 'workflows.search' })}
          fieldSize="md"
          onClear={() => setSearchQuery('')}
        />
      </div>
    );
  };

  const renderWorkflowStarterFilter = () => {
    return (
      <FilterSelect
        isMultiple
        isSearchShown
        placeholderText={formatMessage({ id: 'workflows.filter-no-user' })}
        selectedOptions={workflowStartersIdsFilter}
        optionIdKey="id"
        optionLabelKey="displayName"
        options={workflowStartersOptions}
        onChange={(workflowStarters: number[]) => setWorkflowStartersFilter(workflowStarters)}
        resetFilter={() => setWorkflowStartersFilter([])}
        renderPlaceholder={() => (
          <span className={styles['header-filter']}>{formatMessage({ id: 'workflows.filter-column-starter' })}</span>
        )}
        containerClassname={styles['filter-container']}
        arrowClassName={styles['header-filter__arrow']}
        selectAllLabel={formatMessage({ id: 'workflows.filter-all-users' })}
      />
    );
  };

  const renderStepFilter = () => {
    const STEP_HEADER_NAME = formatMessage({ id: 'workflows.filter-column-step' });
    if (!isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter)) {
      return STEP_HEADER_NAME;
    }

    const [templateIdFilter] = templatesIdsFilter;
    const currentTemplate = filterTemplates.find((t) => t.id === templateIdFilter);
    if (!currentTemplate) {
      return STEP_HEADER_NAME;
    }

    const stepsOptions = currentTemplate.steps
      .map((step) => {
        return {
          ...step,
          name: <StepName initialStepName={step.name} templateId={currentTemplate.id} />,
          subTitle: String(step.number).padStart(2, '0'),
          searchByText: step.name,
        };
      })
      .filter((step) => step.count);

    return (
      <FilterSelect
        isMultiple
        isSearchShown
        placeholderText={formatMessage({ id: 'workflows.filter-no-step' })}
        selectedOptions={stepsIdsFilter}
        optionIdKey="id"
        optionLabelKey="name"
        options={stepsOptions}
        onChange={(steps: number[]) => {
          setStepsFilter(steps);
        }}
        resetFilter={() => {
          setStepsFilter([]);
        }}
        renderPlaceholder={() => <span className={styles['header-filter']}>{STEP_HEADER_NAME}</span>}
        containerClassname={styles['filter-container']}
        arrowClassName={styles['header-filter__arrow']}
        selectAllLabel={formatMessage({ id: 'workflows.filter-all-steps' })}
      />
    );
  };

  const renderPerformersFilter = () => {
    if (statusFilter === EWorkflowsStatus.Snoozed || statusFilter === EWorkflowsStatus.Completed) {
      return formatMessage({ id: 'workflows.filter-column-performers' });
    }

    return (
      <FilterSelect
        isMultiple
        isSearchShown
        placeholderText={formatMessage({ id: 'workflows.filter-no-user' })}
        selectedOptions={performersIdsFilter}
        optionIdKey="id"
        optionLabelKey="displayName"
        options={performersOptions}
        onChange={(users: number[]) => setPerformersFilter(users)}
        resetFilter={() => setPerformersFilter([])}
        renderPlaceholder={() => (
          <span className={styles['header-filter']}>{formatMessage({ id: 'workflows.filter-column-performers' })}</span>
        )}
        containerClassname={styles['filter-container']}
        arrowClassName={styles['header-filter__arrow']}
        selectAllLabel={formatMessage({ id: 'workflows.filter-all-users' })}
      />
    );
  };

  const columns: Column<TableColumns>[] = React.useMemo(
    () => [
      {
        Header: renderSearch(),
        accessor: 'workflow',
        Cell: (props) => (
          <ColumnCells.WorkflowColumn
            {...props}
            onWorkflowEnded={() => removeWorkflowFromList({ workflowId: props.value.id })}
            onWorkflowSnoozed={() => removeWorkflowFromList({ workflowId: props.value.id })}
            onWorkflowDeleted={() => removeWorkflowFromList({ workflowId: props.value.id })}
            onWorkflowResumed={() => removeWorkflowFromList({ workflowId: props.value.id })}
            handleOpenModal={() =>
              openWorkflowLogPopup({
                workflowId: props.value.id,
                shouldSetWorkflowDetailUrl: true,
                redirectTo404IfNotFound: true,
              })
            }
          />
        ),
        width: 336,
      },
      {
        Header: renderWorkflowStarterFilter(),
        accessor: 'starter',
        Cell: ColumnCells.StarterColumn,
        width: 80,
      },
      {
        Header: formatMessage({ id: 'workflows.filter-column-progress' }),
        accessor: 'progress',
        Cell: ColumnCells.ProgressColumn,
        width: 80,
      },
      {
        Header: renderStepFilter(),
        accessor: 'step',
        Cell: ColumnCells.StepColumn,
        width: 272,
      },
      {
        Header: renderPerformersFilter(),
        accessor: 'performer',
        Cell: ColumnCells.PerformerColumn,
        width: 128,
      },
    ],
    [
      searchQuery,
      users.length,
      workflowStartersIdsFilter.length,
      templatesIdsFilter.length,
      filterTemplates,
      stepsIdsFilter.length,
      performersIdsFilter.length,
      statusFilter,
      performersCounters,
      workflowStartersCounters,
    ],
  );

  const data = React.useMemo((): TableColumns[] => {
    return workflowsList.items.map((workflow) => {
      return {
        workflow: workflow,
        starter: workflow,
        progress: workflow,
        step: workflow,
        performer: workflow,
      };
    });
  }, [workflowsList.items]);

  const options: TableOptions<TableColumns> = {
    data,
    columns,
  };

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } = useTable(options);

  const renderTable = () => {
    return (
      <table {...getTableProps()} className={styles['table']}>
        <thead className={styles['thead']}>
          {headerGroups.map((headerGroup) => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column) => (
                <th
                  {...column.getHeaderProps({
                    style: { width: column.width },
                  })}
                  className={styles['column-header']}
                >
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList
            ? renderLoader()
            : rows.map((row) => {
                prepareRow(row);

                const workflowId = row.original.workflow.id;

                return (
                  <tr {...row.getRowProps()} className={styles['row']} key={workflowId}>
                    {row.cells.map((cell) => {
                      return <td {...cell.getCellProps()}>{cell.render('Cell')}</td>;
                    })}
                  </tr>
                );
              })}
        </tbody>
      </table>
    );
  };

  const isListFullLoaded =
    workflowsList.count === workflowsList.items.length &&
    workflowsLoadingStatus !== EWorkflowsLoadingStatus.LoadingNextPage;

  const renderLoader = () => {
    if (!tableWrapperRef.current) {
      return null;
    }

    return createPortal(
      <Loader isLoading isCentered={false} containerClassName={styles['loader']} />,
      tableWrapperRef.current,
    );
  };

  return (
    <div className={styles['container']}>
      <div className={styles['table-wrapper']} ref={tableWrapperRef}>
        <InfiniteScroll
          dataLength={workflowsList.items.length}
          next={() => loadWorkflowsList(workflowsList.items.length)}
          loader={workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingNextPage && renderLoader()}
          hasMore={!isListFullLoaded}
          scrollThreshold="150px"
          className={styles['table-scoll']}
        >
          {renderTable()}
        </InfiniteScroll>

        {workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && (
          <Placeholder
            title={formatMessage({ id: 'workflows.empty-placeholder-title' })}
            description={formatMessage({ id: 'workflows.empty-placeholder-description' })}
            Icon={WorkflowsPlaceholderIcon}
            mood="neutral"
            containerClassName={styles['empty-list-placeholder']}
          />
        )}
      </div>
    </div>
  );
}
