/* eslint-disable consistent-return */
/* eslint-disable indent */
import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { useTable, Column, TableOptions, HeaderGroup } from 'react-table';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import { createPortal } from 'react-dom';
import { debounce } from 'throttle-debounce';
import { useSelector } from 'react-redux';

import classNames from 'classnames';
import { TableColumns } from './types';
import * as ColumnCells from './Columns/Cells';

import { WorkflowsPlaceholderIcon } from '../../WorkflowsPlaceholderIcon';
import { Avatar, FilterSelect, InputField, Loader, Placeholder } from '../../../UI';
import { IApplicationState, IWorkflowsList } from '../../../../types/redux';
import { TOpenWorkflowLogPopupPayload, TRemoveWorkflowFromListPayload } from '../../../../redux/actions';
import { SearchMediumIcon } from '../../../icons';
import { EWorkflowsLoadingStatus, EWorkflowsStatus } from '../../../../types/workflow';
import { IWorkflowsFiltersProps } from '../../types';
import { isArrayWithItems } from '../../../../utils/helpers';
import { canFilterByTemplateStep } from '../../../../utils/workflows/filters';
import { StepName } from '../../../StepName';
import { EXTERNAL_USER, getUserFullName } from '../../../../utils/users';
import { ETemplateOwnerType, ITableViewFields } from '../../../../types/template';
import { useIsTableWiderThanScreen, useWorkflowsTableRef } from './WorkflowsTableContext';

import styles from './WorkflowsTable.css';
import { EColumnWidthMinWidth, ETableViewFieldsWidth } from './Columns/Cells/WorkflowTableConstants';
import { WorkflowsTableActions } from './WorkflowsTableActions';
import { useCheckDevice } from '../../../../hooks/useCheckDevice';
import { createResizeHandler } from './utils/resizeUtils';
import { SKELETON_ROWS } from './constants';
import { defaultSystemColumns } from './Columns/Cells';
import { SkeletonDefaultCell80 } from './Columns/Cells/SystemDefoultColumns';
import { Skeleton } from '../../../UI/Skeleton';

type CustomHeaderGroup<T extends object> = HeaderGroup<T> & {
  columnType: keyof typeof EColumnWidthMinWidth;
  minWidth: number;
};

export interface IWorkflowsTableProps extends IWorkflowsFiltersProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  workflowsList: IWorkflowsList;
  searchText: string;
  onSearch(value: string): void;
  loadWorkflowsList(id: number): void;
  removeWorkflowFromList(payload: TRemoveWorkflowFromListPayload): void;
  openWorkflowLogPopup(payload: TOpenWorkflowLogPopupPayload): void;
}
export interface TableViewContainerRef {
  element: HTMLDivElement | null;
}

export const TableViewContainer = forwardRef<TableViewContainerRef, { children: React.ReactNode }>(
  ({ children }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useImperativeHandle(ref, () => ({
      get element() {
        return containerRef.current;
      },
    }));

    return (
      <div className={styles['table-view-container']} ref={containerRef}>
        {children}
      </div>
    );
  },
);

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
  performersGroupIdsFilter,
  performersCounters,
  statusFilter,
  setWorkflowStartersFilter,
  setStepsFilter,
  onSearch,
  loadWorkflowsList,
  removeWorkflowFromList,
  openWorkflowLogPopup,
  setPerformersFilter,
  setPerformersGroupFilter,
}: IWorkflowsTableProps) {
  const { formatMessage } = useIntl();
  const { isDesktop } = useCheckDevice();
  const groups = useSelector((state: IApplicationState) => state.groups.list);
  const currentUser = useSelector((state: IApplicationState) => state.authUser);
  const [searchQuery, setSearchQuery] = useState(searchText);
  const selectedFields = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.selectedFields);
  const selectedFieldsSet = useMemo(() => new Set(selectedFields), [selectedFields]);

  const savedGlobalWidths = JSON.parse(
    localStorage.getItem(`workflow-column-widths-${currentUser?.id}-global`) || '{}',
  );
  const savedOptionalWidths = JSON.parse(
    localStorage.getItem(`workflow-column-widths-${currentUser?.id}-template-${templatesIdsFilter[0]}`) || '{}',
  );

  const tableWrapperRef = React.useRef<HTMLDivElement | null>(null);
  const tableRef = useRef<HTMLTableElement>(null);

  const tableViewContainerRef = useWorkflowsTableRef();
  const isTableWiderThanScreen = useIsTableWiderThanScreen();
  const debounceOnSearch = useCallback(debounce(500, onSearch), []);

  const [tableHeight, setTableHeight] = useState<number>(0);
  const [colWidths, setColWidths] = useState<Record<string, number>>({});

  useEffect(() => {
    const appContainer = document.getElementById('app-container');
    if (appContainer) {
      appContainer.style.overflow = 'hidden';
    }

    return () => {
      if (appContainer) {
        appContainer.style.overflow = 'scroll';
        appContainer.style.overflowX = 'hidden';
      }
    };
  }, []);

  useEffect(() => {
    debounceOnSearch(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && stepsIdsFilter.length) {
      setStepsFilter([]);
    }
  }, [workflowsLoadingStatus]);

  useEffect(() => {
    if (!tableRef.current) return;
    const observer = new ResizeObserver(([entry]) => {
      setTableHeight(entry.contentRect.height);
    });
    observer.observe(tableRef.current);
    return () => {
      observer.disconnect();
    };
  }, []);

  const workflowStartersOptions = useMemo(() => {
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
        count: workflowStartersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0,
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
          count: performersCounters.find(({ sourceId }) => sourceId === user.id)?.workflowsCount || 0,
          searchByText: userFullName,
        };
      }),
    [users.length, performersCounters],
  );

  const performersGroupOptions = React.useMemo(
    () =>
      groups.map((group) => {
        return {
          ...group,
          type: ETemplateOwnerType.UserGroup,
          displayName: (
            <div className={styles['user']}>
              <Avatar user={{ type: ETemplateOwnerType.UserGroup }} size="sm" />
              <span className={styles['user-name']}>{group.name}</span>
            </div>
          ),
          count: performersCounters.find(({ sourceId }) => sourceId === group.id)?.workflowsCount || 0,
          searchByText: group.name,
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
        selectedOptions={[...performersGroupIdsFilter, ...performersIdsFilter]}
        optionIdKey="id"
        optionLabelKey="displayName"
        options={[...performersGroupOptions, ...performersOptions]}
        onChange={(_, options: any) => {
          const performers = options
            .filter((item: any) => item.type === ETemplateOwnerType.User)
            .map((lItem: any) => lItem.id);
          const selectedGroups = options
            .filter((item: any) => item.type === ETemplateOwnerType.UserGroup)
            .map((lItem: any) => lItem.id);

          setPerformersFilter(performers);
          setPerformersGroupFilter(selectedGroups);
        }}
        resetFilter={() => {
          setPerformersFilter([]);
          setPerformersGroupFilter([]);
        }}
        renderPlaceholder={() => (
          <span className={styles['header-filter']}>{formatMessage({ id: 'workflows.filter-column-performers' })}</span>
        )}
        containerClassname={styles['filter-container']}
        arrowClassName={styles['header-filter__arrow']}
        selectAllLabel={formatMessage({ id: 'workflows.filter-all-users' })}
      />
    );
  };

  const renderWorkflowColumn = useCallback(
    (props) => (
      <ColumnCells.WorkflowColumn
        {...props}
        onWorkflowEnded={() => loadWorkflowsList(0)}
        onWorkflowDeleted={() => removeWorkflowFromList({ workflowId: props.value.id })}
        handleOpenModal={() =>
          openWorkflowLogPopup({
            workflowId: props.value.id,
            shouldSetWorkflowDetailUrl: true,
            redirectTo404IfNotFound: true,
          })
        }
      />
    ),
    [loadWorkflowsList, removeWorkflowFromList, openWorkflowLogPopup],
  );

  const fieldsColumns: Column<TableColumns>[] =
    workflowsList?.items?.[0]?.fields?.map((field: ITableViewFields) => ({
      Header: <div className={styles['column-header__title']}>{field.name}</div>,
      accessor: field.apiName,
      Cell: ColumnCells.OptionalFieldColumn,
      width: savedOptionalWidths[field.apiName] || ETableViewFieldsWidth[field.type],
      columnType: field.type,
      minWidth: EColumnWidthMinWidth[field.type],
    })) || [];

  const previousColumnsRef = useRef<Column<TableColumns>[]>(defaultSystemColumns);

  const columns: Column<TableColumns>[] = React.useMemo(() => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList) {
      return previousColumnsRef.current;
    }

    const newColumns = [
      ...(selectedFieldsSet.has('workflow')
        ? [
            {
              Header: renderSearch(),
              accessor: 'workflow',
              Cell: renderWorkflowColumn,
              width: savedGlobalWidths.workflow || ETableViewFieldsWidth.workflow,
              minWidth: EColumnWidthMinWidth.workflow,
              columnType: 'workflow',
            },
          ]
        : []),
      ...(selectedFieldsSet.has('templateName')
        ? [
            {
              Header: (
                <div className={styles['column-header__template-name']}>
                  {formatMessage({ id: 'workflows.filter-column-template-name' })}
                </div>
              ),
              accessor: 'templateName',
              Cell: ColumnCells.TemplateNameColumn,
              width: savedGlobalWidths.templateName || ETableViewFieldsWidth.templateName,
              minWidth: EColumnWidthMinWidth.templateName,
              columnType: 'templateName',
            },
          ]
        : []),
      ...(selectedFieldsSet.has('starter')
        ? [
            {
              Header: renderWorkflowStarterFilter(),
              accessor: 'starter',
              Cell: ColumnCells.StarterColumn,
              width: savedGlobalWidths.starter || ETableViewFieldsWidth.starter,
              minWidth: EColumnWidthMinWidth.starter,
              columnType: 'starter',
            },
          ]
        : []),
      ...(selectedFieldsSet.has('progress')
        ? [
            {
              Header: formatMessage({ id: 'workflows.filter-column-progress' }),
              accessor: 'progress',
              Cell: ColumnCells.ProgressColumn,
              width: savedGlobalWidths.progress || ETableViewFieldsWidth.progress,
              minWidth: EColumnWidthMinWidth.progress,
              columnType: 'progress',
            },
          ]
        : []),
      ...(selectedFieldsSet.has('step')
        ? [
            {
              Header: renderStepFilter(),
              accessor: 'step',
              Cell: ColumnCells.StepColumn,
              width: savedGlobalWidths.step || ETableViewFieldsWidth.step,
              minWidth: EColumnWidthMinWidth.step,
              columnType: 'step',
            },
          ]
        : []),
      ...(selectedFieldsSet.has('performer')
        ? [
            {
              Header: renderPerformersFilter(),
              accessor: 'performer',
              Cell: ColumnCells.PerformerColumn,
              width: savedGlobalWidths.performer || ETableViewFieldsWidth.performer,
              minWidth: EColumnWidthMinWidth.performer,
              columnType: 'performer',
            },
          ]
        : []),
      ...fieldsColumns,
    ];
    previousColumnsRef.current = newColumns;
    return newColumns;
  }, [
    workflowsLoadingStatus,
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
    fieldsColumns.length,
    selectedFieldsSet,
  ]);

  const data = useMemo((): TableColumns[] => {
    return workflowsList.items.map((workflow) => {
      const baseData: TableColumns = {
        workflow,
        templateName: workflow,
        starter: workflow,
        progress: workflow,
        step: workflow,
        performer: workflow,
      } as TableColumns;

      workflow.fields?.forEach((field: ITableViewFields) => {
        baseData[field.apiName] = field;
      });

      return baseData;
    });
  }, [workflowsList.items]);

  const options: TableOptions<TableColumns> = {
    data,
    columns,
  };

  useEffect(() => {
    if (workflowsLoadingStatus === EWorkflowsLoadingStatus.Loaded) {
      setColWidths((prev) => {
        const newWidths = { ...prev };

        columns.forEach((col) => {
          const id = col.accessor as string;
          if (!newWidths[id]) {
            newWidths[id] = col.width as number;
          }
        });

        return newWidths;
      });
    }
  }, [columns.length, workflowsLoadingStatus]);

  const handleMouseDown = createResizeHandler(colWidths, setColWidths, currentUser?.id, templatesIdsFilter[0]);

  const { getTableProps, getTableBodyProps, headerGroups, rows, prepareRow } = useTable<TableColumns>(options);

  const shouldSkeletonTable =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList && workflowsList.items.length === 0;

  const shouldSkeleton =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList && workflowsList.items.length > 0;

  const renderTable = () => {
    return (
      <table {...getTableProps()} className={styles['table']} ref={tableRef}>
        <thead className={styles['thead']}>
          {shouldSkeletonTable ? (
            <tr>
              {defaultSystemColumns.map((column) => (
                <th
                  key={column.accessor as string}
                  style={{
                    position: 'relative',
                    width: (column as any).width,
                    maxWidth: (column as any).width,
                    minWidth: (column as any).width,
                  }}
                  className={classNames(styles['column-header'], styles['column'])}
                >
                  {(column as any).Header}
                </th>
              ))}
            </tr>
          ) : (
            headerGroups.map((headerGroup) => (
              <tr {...headerGroup.getHeaderGroupProps()}>
                {headerGroup.headers.map((column: CustomHeaderGroup<TableColumns>) => (
                  <th
                    {...column.getHeaderProps({
                      style: {
                        position: 'relative',
                        width: colWidths[column.id],
                        maxWidth: colWidths[column.id],
                        minWidth: colWidths[column.id],
                      },
                    })}
                    className={classNames(styles['column-header'], styles['column'])}
                  >
                    {shouldSkeleton ? <SkeletonDefaultCell80 /> : column.render('Header')}
                    <div className={styles['column-header__hover-zone']} style={{ height: tableHeight }}>
                      <div
                        className={styles['column-header__resize']}
                        style={{ height: tableHeight }}
                        onMouseDown={(e) => handleMouseDown(e, column.id, column.minWidth)}
                        role="button"
                        aria-label={`Resize column ${column.id}`}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                          }
                        }}
                      >
                        <div className={styles['column-header__dashed-line']} style={{ height: tableHeight }}></div>
                      </div>
                    </div>
                  </th>
                ))}
              </tr>
            ))
          )}
        </thead>
        <tbody {...getTableBodyProps()}>
          {shouldSkeletonTable
            ? SKELETON_ROWS.map((row) => (
                <tr className={styles['row']} key={row}>
                  {defaultSystemColumns.map((column) => (
                    <td key={column.accessor as string} className={styles['column']}>
                      {(column as any).Cell({})}
                    </td>
                  ))}
                </tr>
              ))
            : rows.map((row) => {
                prepareRow(row);

                const workflowId = row.original.workflow.id;

                return (
                  <tr {...row.getRowProps()} className={styles['row']} key={workflowId}>
                    {row.cells.map((cell) => {
                      return (
                        <td
                          {...cell.getCellProps({
                            style: {
                              width: colWidths[cell.column.id],
                              maxWidth: colWidths[cell.column.id],
                              minWidth: colWidths[cell.column.id],
                            },
                          })}
                          className={styles['column']}
                        >
                          {shouldSkeleton ? (
                            <Skeleton width={`${Math.max(colWidths[cell.column.id] * 0.7, 80)}px`} height="2rem" />
                          ) : (
                            cell.render('Cell')
                          )}
                        </td>
                      );
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
    <TableViewContainer ref={tableViewContainerRef}>
      {!isTableWiderThanScreen && isDesktop && (
        <WorkflowsTableActions workflowsLoadingStatus={workflowsLoadingStatus} />
      )}
      <div
        className={classNames(
          styles['table-wrapper'],
          isTableWiderThanScreen && styles['table-wrapper--narrow-mobile'],
        )}
        ref={tableWrapperRef}
      >
        <InfiniteScroll
          dataLength={workflowsList.items.length}
          next={() => loadWorkflowsList(workflowsList.items.length)}
          loader={workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingNextPage && renderLoader()}
          hasMore={!isListFullLoaded}
          scrollThreshold="150px"
          className={styles['table-scoll']}
          scrollableTarget="workflows-main"
        >
          {renderTable()}
        </InfiniteScroll>

        {workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList && (
          <Placeholder
            title={formatMessage({ id: 'workflows.empty-placeholder-title' })}
            description={formatMessage({ id: 'workflows.empty-placeholder-description' })}
            Icon={WorkflowsPlaceholderIcon}
            mood="neutral"
            containerClassName={classNames(
              styles['empty-list-placeholder'],
              isTableWiderThanScreen && styles['empty-list-placeholder--wide'],
            )}
          />
        )}
      </div>
    </TableViewContainer>
  );
}
