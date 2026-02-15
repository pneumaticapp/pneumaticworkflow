import React, {
  forwardRef,
  ReactNode,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useTable, Column, TableOptions, HeaderGroup } from 'react-table';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import { createPortal } from 'react-dom';
import { debounce } from 'throttle-debounce';
import { useSelector } from 'react-redux';

import classNames from 'classnames';
import { TableColumns } from './types';
import * as ColumnCells from './Columns/Cells';

import { createWorkflowsPlaceholderIcon } from '../../WorkflowsPlaceholderIcon';
import { InputField, Loader, Placeholder } from '../../../UI';
import { IWorkflowsList } from '../../../../types/redux';
import { TOpenWorkflowLogPopupPayload, TRemoveWorkflowFromListPayload } from '../../../../redux/workflows/types';
import { SearchMediumIcon } from '../../../icons';
import { EWorkflowsLoadingStatus } from '../../../../types/workflow';
import { IWorkflowsFiltersProps } from '../../types';
import { ITableViewFields } from '../../../../types/template';
import { useIsTableWiderThanScreen, useWorkflowsTableRef } from './WorkflowsTableContext';

import styles from './WorkflowsTable.css';
import { EColumnWidthMinWidth, ETableViewFieldsWidth } from './Columns/Cells/WorkflowTableConstants';
import { WorkflowsTableActions } from './WorkflowsTableActions';
import { useCheckDevice } from '../../../../hooks/useCheckDevice';
import { createResizeHandler } from './utils/resizeUtils';
import { ALL_SYSTEM_FIELD_NAMES, SKELETON_ROWS } from './constants';
import { defaultSystemSkeletonTable } from './Columns/Cells';
import { SkeletonDefaultCell80 } from './Columns/Cells/SystemDefaultColumns';
import { Skeleton } from '../../../UI/Skeleton';
import { getCurrentUser } from '../../../../redux/selectors/authUser';
import { getLastLoadedTemplateIdForTable, getSavedFields } from '../../../../redux/selectors/workflows';

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

export const TableViewContainer = forwardRef<TableViewContainerRef, { children: ReactNode }>(({ children }, ref) => {
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
});

export function WorkflowsTable({
  templatesIdsFilter,
  workflowsLoadingStatus,
  workflowsList,
  searchText,
  users,
  workflowStartersCounters,
  workflowStartersIdsFilter,
  tasksApiNamesFilter,
  filterTemplates,
  performersIdsFilter,
  performersCounters,
  statusFilter,
  onSearch,
  loadWorkflowsList,
  removeWorkflowFromList,
  openWorkflowLogPopup,
}: IWorkflowsTableProps) {
  const { formatMessage } = useIntl();
  const { isDesktop, isMobile } = useCheckDevice();

  const currentUser = useSelector(getCurrentUser);
  const selectedFields = useSelector(getSavedFields);
  const lastLoadedTemplateIdForTable = useSelector(getLastLoadedTemplateIdForTable);

  const selectedFieldsSet = useMemo(() => new Set(selectedFields), [selectedFields]);

  const savedGlobalWidths = JSON.parse(
    localStorage.getItem(`workflow-column-widths-${currentUser?.id}-global`) || '{}',
  );
  const savedOptionalWidths = JSON.parse(
    localStorage.getItem(`workflow-column-widths-${currentUser?.id}-template-${templatesIdsFilter[0]}`) || '{}',
  );

  const tableWrapperRef = useRef<HTMLDivElement | null>(null);
  const tableRef = useRef<HTMLTableElement>(null);
  const cashTableStructureRef = useRef<Column<TableColumns>[]>([]);

  const tableViewContainerRef = useWorkflowsTableRef();
  const isTableWiderThanScreen = useIsTableWiderThanScreen();
  const debounceOnSearch = useCallback(debounce(500, onSearch), []);

  const currentTemplateId = templatesIdsFilter.length === 1 ? templatesIdsFilter[0] : null;
  const [searchQuery, setSearchQuery] = useState(searchText);
  const [tableHeight, setTableHeight] = useState<number>(0);
  const [colWidths, setColWidths] = useState<Record<string, number>>({});
  const [isChangeTemplateId, setIsChangeTemplateId] = useState(false);
  
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
    if (!tableRef.current) return undefined;

    const observer = new ResizeObserver(([entry]) => {
      setTableHeight(entry.contentRect.height);
    });
    observer.observe(tableRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (String(lastLoadedTemplateIdForTable) !== String(currentTemplateId)) {
      setIsChangeTemplateId(true);
    } else {
      setIsChangeTemplateId(false);
    }
  }, [currentTemplateId]);

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

  const shouldSkeletonDefaultTable =
    (workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList || selectedFields.length === 0) &&
    cashTableStructureRef.current.length === 0;

  const shouldSkeletonOptionalTable =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList && isChangeTemplateId;

  const shouldSkeletonBody =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList &&
    String(lastLoadedTemplateIdForTable) === String(currentTemplateId);

  const isWorkflowEmptyList =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList ||
    (workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList &&
      workflowsList.items.length === 0 &&
      String(lastLoadedTemplateIdForTable) === String(currentTemplateId));

  const columns: Column<TableColumns>[] = useMemo(() => {
    if (shouldSkeletonOptionalTable) {
      return cashTableStructureRef.current;
    }

    const systemColumns = [
      ...(selectedFieldsSet.has('system-column-workflow')
        ? [
          {
            Header: renderSearch(),
            accessor: 'system-column-workflow',
            Cell: renderWorkflowColumn,
            width: savedGlobalWidths['system-column-workflow'] || ETableViewFieldsWidth['system-column-workflow'],
            minWidth: EColumnWidthMinWidth['system-column-workflow'],
            columnType: 'system-column-workflow',
          },
        ]
        : []),
      ...(selectedFieldsSet.has('system-column-templateName')
        ? [
          {
            Header: (
                <div className={styles['column-header__template-name']}>
                  {formatMessage({ id: 'workflows.filter-column-template-name' })}
                </div>
            ),
            accessor: 'system-column-templateName',
            Cell: ColumnCells.TemplateNameColumn,
            width:
                savedGlobalWidths['system-column-templateName'] || ETableViewFieldsWidth['system-column-templateName'],
            minWidth: EColumnWidthMinWidth['system-column-templateName'],
            columnType: 'system-column-templateName',
          },
        ]
        : []),
      ...(selectedFieldsSet.has('system-column-starter')
        ? [
          {
            Header: (
                <div className={styles['column-header__starter-name']}>
                  {formatMessage({ id: 'workflows.filter-column-starter' })}
                </div>
            ),
            accessor: 'system-column-starter',
            Cell: ColumnCells.StarterColumn,
            width: savedGlobalWidths['system-column-starter'] || ETableViewFieldsWidth['system-column-starter'],
            minWidth: EColumnWidthMinWidth['system-column-starter'],
            columnType: 'system-column-starter',
          },
        ]
        : []),
      ...(selectedFieldsSet.has('system-column-progress')
        ? [
          {
            Header: formatMessage({ id: 'workflows.filter-column-progress' }),
            accessor: 'system-column-progress',
            Cell: ColumnCells.ProgressColumn,
            width: savedGlobalWidths['system-column-progress'] || ETableViewFieldsWidth['system-column-progress'],
            minWidth: EColumnWidthMinWidth['system-column-progress'],
            columnType: 'system-column-progress',
          },
        ]
        : []),
      ...(selectedFieldsSet.has('system-column-step')
        ? [
          {
            Header: (
                <div className={styles['column-header__task-name']}>
                  {formatMessage({ id: 'workflows.filter-column-tasks' })}
                </div>
            ),
            accessor: 'system-column-step',
            Cell: ColumnCells.TaskColumn,
            width: savedGlobalWidths['system-column-step'] || ETableViewFieldsWidth['system-column-step'],
            minWidth: EColumnWidthMinWidth['system-column-step'],
            columnType: 'system-column-step',
          },
        ]
        : []),
      ...(selectedFieldsSet.has('system-column-performer')
        ? [
          {
            Header: (
                <div className={styles['column-header__performer-name']}>
                  {formatMessage({ id: 'workflows.filter-column-performers' })}
                </div>
            ),
            accessor: 'system-column-performer',
            Cell: ColumnCells.PerformerColumn,
            width: savedGlobalWidths['system-column-performer'] || ETableViewFieldsWidth['system-column-performer'],
            minWidth: EColumnWidthMinWidth['system-column-performer'],
            columnType: 'system-column-performer',
          },
        ]
        : []),
    ];

    const optionalColumns = isWorkflowEmptyList
      ? cashTableStructureRef.current.filter((col) => !new Set(ALL_SYSTEM_FIELD_NAMES).has(col.accessor as string))
      : fieldsColumns;

    const newColumns = [...systemColumns, ...optionalColumns];

    if (
      workflowsLoadingStatus === EWorkflowsLoadingStatus.Loaded ||
      workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList
    ) {
      cashTableStructureRef.current = newColumns;
      setIsChangeTemplateId(false);
    }

    return newColumns;
  }, [
    workflowsLoadingStatus,
    searchQuery,
    users.length,
    workflowStartersIdsFilter.length,
    templatesIdsFilter.length,
    filterTemplates,
    tasksApiNamesFilter.length,
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
        'system-column-workflow': workflow,
        'system-column-templateName': workflow,
        'system-column-starter': workflow,
        'system-column-progress': workflow,
        'system-column-step': workflow,
        'system-column-performer': workflow,
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

  const getTableBodyContent = () => {
    if (shouldSkeletonDefaultTable) {
      return SKELETON_ROWS.map((row) => (
        <tr className={styles['row']} key={row}>
          {defaultSystemSkeletonTable.map((column) => (
            <td key={column.accessor as string} className={styles['column']}>
              {(column as any).Cell({})}
            </td>
          ))}
        </tr>
      ));
    }
    if (workflowsList.items.length === 0 && (shouldSkeletonBody || shouldSkeletonOptionalTable)) {
      return SKELETON_ROWS.map((row) => (
        <tr className={styles['row']} key={row}>
          {columns.map((column) => {
            return (
              <td key={column.accessor as string} className={styles['column']} aria-label="Loading">
                <Skeleton
                  width={`${(column as any).width ? Math.max((column as any).width * 0.7, 80) : 80}px`}
                  height="2rem"
                />
              </td>
            );
          })}
        </tr>
      ));
    }

    return rows.map((row) => {
      prepareRow(row);
      const workflowId = row.original['system-column-workflow'].id;
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
                {shouldSkeletonOptionalTable || shouldSkeletonBody ? (
                  <Skeleton
                    width={`${
                      cell.column.id && colWidths[cell.column.id] ? Math.max(colWidths[cell.column.id] * 0.7, 80) : 80
                    }px`}
                    height="2rem"
                  />
                ) : (
                  cell.render('Cell')
                )}
              </td>
            );
          })}
        </tr>
      );
    });
  };

  const renderTable = () => {
    return (
      <table {...getTableProps()} className={styles['table']} ref={tableRef}>
        <thead className={styles['thead']}>
          {shouldSkeletonDefaultTable ? (
            <tr>
              {defaultSystemSkeletonTable.map((column) => (
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
                    {shouldSkeletonOptionalTable ? <SkeletonDefaultCell80 /> : column.render('Header')}
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
        <tbody {...getTableBodyProps()}>{getTableBodyContent()}</tbody>
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
            Icon={() => createWorkflowsPlaceholderIcon(isMobile)}
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
