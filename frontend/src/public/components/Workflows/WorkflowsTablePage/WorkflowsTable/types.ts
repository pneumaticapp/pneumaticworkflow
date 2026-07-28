import { MouseEvent, ReactNode, RefObject } from 'react';
import { Column, HeaderGroup, TableInstance } from 'react-table';

import { ITableViewFields } from '../../../../types/template';
import { EWorkflowsLoadingStatus, IWorkflowClient } from '../../../../types/workflow';
import { IWorkflowsList } from '../../../../types/redux';
import { TOpenWorkflowLogPopupPayload, TRemoveWorkflowFromListPayload } from '../../../../redux/workflows/types';
import { IWorkflowsFiltersProps } from '../../types';
import { EColumnWidthMinWidth } from './Columns/Cells/WorkflowTableConstants';

export type TableColumns = {
  'system-column-workflow': IWorkflowClient;
  'system-column-templateName': IWorkflowClient;
  'system-column-starter': IWorkflowClient;
  'system-column-progress': IWorkflowClient;
  'system-column-step': IWorkflowClient;
  'system-column-performer': IWorkflowClient;
} & {
  [key: string]: ITableViewFields;
};

export type TSystemField = {
  apiName: string;
  name: string;
  isDisabled: boolean;
  hasNotTooltip: boolean;
};

export type WorkflowColumn = Column<TableColumns> & {
  columnType: keyof typeof EColumnWidthMinWidth;
};

export type CustomHeaderGroup<T extends object> = HeaderGroup<T> & {
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

export interface TableViewContainerProps {
  children: ReactNode;
}

export interface WorkflowsTableGridProps {
  table: TableInstance<TableColumns>;
  tableRef: RefObject<HTMLTableElement>;
  tableHeight: number;
  columns: Column<TableColumns>[];
  colWidths: Record<string, number>;
  handleMouseDown(event: MouseEvent, columnId: string, minWidth: number): void;
  itemsCount: number;
  shouldSkeletonBody: boolean;
  shouldSkeletonDefaultTable: boolean;
  shouldSkeletonOptionalTable: boolean;
}

export interface WorkflowsTableActionsProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  isWideTable?: boolean;
  isMobile?: boolean;
}