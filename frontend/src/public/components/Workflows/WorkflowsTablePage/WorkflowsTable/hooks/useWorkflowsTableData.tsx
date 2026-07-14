import React, { ReactElement, useEffect, useMemo, useRef, useState } from 'react';
import { CellProps } from 'react-table';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { ITableViewFields } from '../../../../../types/template';
import { EWorkflowsLoadingStatus } from '../../../../../types/workflow';
import { IWorkflowsList } from '../../../../../types/redux';
import { getCurrentUser } from '../../../../../redux/selectors/authUser';
import {
  getLastLoadedTemplateIdForTable,
  getSavedFields,
} from '../../../../../redux/selectors/workflows';
import * as ColumnCells from '../Columns/Cells';
import {
  EColumnWidthMinWidth,
  ETableViewFieldsWidth,
} from '../Columns/Cells/WorkflowTableConstants';
import { ALL_SYSTEM_FIELD_NAMES } from '../constants';
import { TableColumns, WorkflowColumn } from '../types';
import { useSavedColumnWidths } from './useWorkflowColumnWidths';

import styles from '../WorkflowsTable.css';

type TUseWorkflowsTableDataParams = {
  workflowsList: IWorkflowsList;
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  templatesIdsFilter: number[];
  searchHeader: ReactElement;
  renderWorkflowColumn(props: CellProps<TableColumns>): ReactElement;
};

export function useWorkflowsTableData({
  workflowsList,
  workflowsLoadingStatus,
  templatesIdsFilter,
  searchHeader,
  renderWorkflowColumn,
}: TUseWorkflowsTableDataParams) {
  const { formatMessage } = useIntl();
  const currentUser = useSelector(getCurrentUser);
  const selectedFields = useSelector(getSavedFields);
  const lastLoadedTemplateId = useSelector(getLastLoadedTemplateIdForTable);
  const cachedColumnsRef = useRef<WorkflowColumn[]>([]);
  const [isTemplateChanging, setIsTemplateChanging] = useState(false);
  const currentTemplateId = templatesIdsFilter.length === 1 ? templatesIdsFilter[0] : undefined;
  const selectedFieldsSet = useMemo(() => new Set(selectedFields), [selectedFields]);
  const maxPerformersCount = useMemo(
    () => workflowsList.items.reduce(
      (maximum, workflow) => Math.max(maximum, workflow.selectedUsers?.length ?? 0),
      0,
    ),
    [workflowsList.items],
  );
  const {
    savedGlobalWidths,
    savedOptionalWidths,
    performerColumnMinWidth,
    performerColumnWidth,
  } = useSavedColumnWidths({
    currentUserId: currentUser?.id,
    templateId: currentTemplateId,
    maxPerformersCount,
  });

  useEffect(() => {
    setIsTemplateChanging(String(lastLoadedTemplateId) !== String(currentTemplateId ?? null));
  }, [currentTemplateId, lastLoadedTemplateId]);

  const fieldsColumns = useMemo<WorkflowColumn[]>(
    () => workflowsList.items[0]?.fields?.map((field: ITableViewFields) => ({
      Header: <div className={styles['column-header__title']}>{field.name}</div>,
      accessor: field.apiName,
      Cell: ColumnCells.OptionalFieldColumn,
      width: savedOptionalWidths[field.apiName] || ETableViewFieldsWidth[field.type],
      columnType: field.type,
      minWidth: EColumnWidthMinWidth[field.type],
    })) || [],
    [savedOptionalWidths, workflowsList.items],
  );

  const shouldSkeletonDefaultTable = (
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList
    || selectedFields.length === 0
  ) && cachedColumnsRef.current.length === 0;
  const shouldSkeletonOptionalTable =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList && isTemplateChanging;
  const shouldSkeletonBody =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList
    && String(lastLoadedTemplateId) === String(currentTemplateId ?? null);
  const isWorkflowEmptyList =
    workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList
    || (
      workflowsLoadingStatus === EWorkflowsLoadingStatus.LoadingList
      && workflowsList.items.length === 0
      && String(lastLoadedTemplateId) === String(currentTemplateId ?? null)
    );

  const columns = useMemo<WorkflowColumn[]>(() => {
    if (shouldSkeletonOptionalTable) {
      return cachedColumnsRef.current;
    }

    const systemColumns: WorkflowColumn[] = [
      ...(selectedFieldsSet.has('system-column-workflow')
        ? [{
          Header: searchHeader,
          accessor: 'system-column-workflow' as const,
          Cell: renderWorkflowColumn,
          width: savedGlobalWidths['system-column-workflow']
            || ETableViewFieldsWidth['system-column-workflow'],
          minWidth: EColumnWidthMinWidth['system-column-workflow'],
          columnType: 'system-column-workflow' as const,
        }]
        : []),
      ...(selectedFieldsSet.has('system-column-templateName')
        ? [{
          Header: (
            <div className={styles['column-header__template-name']}>
              {formatMessage({ id: 'workflows.filter-column-template-name' })}
            </div>
          ),
          accessor: 'system-column-templateName' as const,
          Cell: ColumnCells.TemplateNameColumn,
          width: savedGlobalWidths['system-column-templateName']
            || ETableViewFieldsWidth['system-column-templateName'],
          minWidth: EColumnWidthMinWidth['system-column-templateName'],
          columnType: 'system-column-templateName' as const,
        }]
        : []),
      ...(selectedFieldsSet.has('system-column-starter')
        ? [{
          Header: (
            <div className={styles['column-header__starter-name']}>
              {formatMessage({ id: 'workflows.filter-column-starter' })}
            </div>
          ),
          accessor: 'system-column-starter' as const,
          Cell: ColumnCells.StarterColumn,
          width: savedGlobalWidths['system-column-starter']
            || ETableViewFieldsWidth['system-column-starter'],
          minWidth: EColumnWidthMinWidth['system-column-starter'],
          columnType: 'system-column-starter' as const,
        }]
        : []),
      ...(selectedFieldsSet.has('system-column-progress')
        ? [{
          Header: formatMessage({ id: 'workflows.filter-column-progress' }),
          accessor: 'system-column-progress' as const,
          Cell: ColumnCells.ProgressColumn,
          width: savedGlobalWidths['system-column-progress']
            || ETableViewFieldsWidth['system-column-progress'],
          minWidth: EColumnWidthMinWidth['system-column-progress'],
          columnType: 'system-column-progress' as const,
        }]
        : []),
      ...(selectedFieldsSet.has('system-column-step')
        ? [{
          Header: (
            <div className={styles['column-header__task-name']}>
              {formatMessage({ id: 'workflows.filter-column-tasks' })}
            </div>
          ),
          accessor: 'system-column-step' as const,
          Cell: ColumnCells.TaskColumn,
          width: savedGlobalWidths['system-column-step']
            || ETableViewFieldsWidth['system-column-step'],
          minWidth: EColumnWidthMinWidth['system-column-step'],
          columnType: 'system-column-step' as const,
        }]
        : []),
      ...(selectedFieldsSet.has('system-column-performer')
        ? [{
          Header: (
            <div className={styles['column-header__performer-name']}>
              {formatMessage({ id: 'workflows.filter-column-performers' })}
            </div>
          ),
          accessor: 'system-column-performer' as const,
          Cell: ColumnCells.PerformerColumn,
          width: performerColumnWidth,
          minWidth: performerColumnMinWidth,
          columnType: 'system-column-performer' as const,
        }]
        : []),
    ];
    const systemFieldNames = new Set<string>(ALL_SYSTEM_FIELD_NAMES);
    const optionalColumns = isWorkflowEmptyList
      ? cachedColumnsRef.current.filter((column) => !systemFieldNames.has(column.accessor as string))
      : fieldsColumns;

    return [...systemColumns, ...optionalColumns];
  }, [
    fieldsColumns,
    formatMessage,
    isWorkflowEmptyList,
    performerColumnMinWidth,
    performerColumnWidth,
    renderWorkflowColumn,
    savedGlobalWidths,
    searchHeader,
    selectedFieldsSet,
    shouldSkeletonOptionalTable,
  ]);

  useEffect(() => {
    if (
      workflowsLoadingStatus === EWorkflowsLoadingStatus.Loaded
      || workflowsLoadingStatus === EWorkflowsLoadingStatus.EmptyList
    ) {
      cachedColumnsRef.current = columns;
      setIsTemplateChanging(false);
    }
  }, [columns, workflowsLoadingStatus]);

  const data = useMemo<TableColumns[]>(() => workflowsList.items.map((workflow) => {
    const row = {
      'system-column-workflow': workflow,
      'system-column-templateName': workflow,
      'system-column-starter': workflow,
      'system-column-progress': workflow,
      'system-column-step': workflow,
      'system-column-performer': workflow,
    } as TableColumns;

    workflow.fields?.forEach((field: ITableViewFields) => {
      row[field.apiName] = field;
    });

    return row;
  }), [workflowsList.items]);

  return {
    columns,
    currentTemplateId,
    currentUserId: currentUser?.id,
    data,
    shouldSkeletonBody,
    shouldSkeletonDefaultTable,
    shouldSkeletonOptionalTable,
  };
}
