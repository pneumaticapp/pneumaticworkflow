import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTable, CellProps, TableOptions } from 'react-table';
import InfiniteScroll from 'react-infinite-scroll-component';
import { useIntl } from 'react-intl';
import { createPortal } from 'react-dom';
import { debounce } from 'throttle-debounce';
import classNames from 'classnames';
import { IWorkflowsTableProps, TableColumns } from './types';
import * as ColumnCells from './Columns/Cells';

import { createWorkflowsPlaceholderIcon } from '../../WorkflowsPlaceholderIcon';
import { InputField, Loader, Placeholder } from '../../../UI';
import { SearchMediumIcon } from '../../../icons';
import { EWorkflowsLoadingStatus } from '../../../../types/workflow';
import { useIsTableWiderThanScreen, useWorkflowsTableRef } from './WorkflowsTableContext';

import styles from './WorkflowsTable.css';
import { WorkflowsTableActions } from './WorkflowsTableActions';
import { useCheckDevice } from '../../../../hooks/useCheckDevice';
import { useWorkflowColumnWidths } from './hooks/useWorkflowColumnWidths';
import { useWorkflowsTableData } from './hooks/useWorkflowsTableData';
import { TableViewContainer } from './TableViewContainer';
import { WorkflowsTableGrid } from './WorkflowsTableGrid';

export function WorkflowsTable({
  templatesIdsFilter,
  workflowsLoadingStatus,
  workflowsList,
  searchText,
  onSearch,
  loadWorkflowsList,
  removeWorkflowFromList,
  openWorkflowLogPopup,
}: IWorkflowsTableProps) {
  const { formatMessage } = useIntl();
  const { isDesktop } = useCheckDevice();

  const tableWrapperRef = useRef<HTMLDivElement | null>(null);
  const tableRef = useRef<HTMLTableElement>(null);
  const tableViewContainerRef = useWorkflowsTableRef();
  const isTableWiderThanScreen = useIsTableWiderThanScreen();
  const debounceOnSearch = useCallback(debounce(500, onSearch), []);

  const [searchQuery, setSearchQuery] = useState(searchText);
  const [tableHeight, setTableHeight] = useState<number>(0);
  const { isMobile } = useCheckDevice();
  
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

  const searchHeader = useMemo(() => (
    <div className={styles['search']}>
      <SearchMediumIcon className={styles['search__icon']} />
      <InputField
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.currentTarget.value)}
        className={styles['search-field__input']}
        placeholder={formatMessage({ id: 'workflows.search' })}
        fieldSize="md"
        onClear={() => setSearchQuery('')}
      />
    </div>
  ), [formatMessage, searchQuery]);

  const renderWorkflowColumn = useCallback(
    (props: CellProps<TableColumns>) => (
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

  const {
    columns,
    currentTemplateId,
    currentUserId,
    data,
    shouldSkeletonBody,
    shouldSkeletonDefaultTable,
    shouldSkeletonOptionalTable,
  } = useWorkflowsTableData({
    workflowsList,
    workflowsLoadingStatus,
    templatesIdsFilter,
    searchHeader,
    renderWorkflowColumn,
  });

  const options: TableOptions<TableColumns> = {
    data,
    columns,
  };

  const { colWidths, handleMouseDown } = useWorkflowColumnWidths({
    columns,
    workflowsLoadingStatus,
    currentUserId,
    templateId: currentTemplateId,
  });

  const table = useTable<TableColumns>(options);

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
          <WorkflowsTableGrid
            table={table}
            tableRef={tableRef}
            tableHeight={tableHeight}
            columns={columns}
            colWidths={colWidths}
            handleMouseDown={handleMouseDown}
            itemsCount={workflowsList.items.length}
            shouldSkeletonBody={shouldSkeletonBody}
            shouldSkeletonDefaultTable={shouldSkeletonDefaultTable}
            shouldSkeletonOptionalTable={shouldSkeletonOptionalTable}
          />
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
