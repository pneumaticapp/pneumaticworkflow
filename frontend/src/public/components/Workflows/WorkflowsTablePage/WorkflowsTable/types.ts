import type { MouseEvent, ReactNode, RefObject } from 'react';
import type { Column, HeaderGroup, TableInstance } from 'react-table';

import type { ITableViewFields } from '../../../../types/template';
import type { EWorkflowsLoadingStatus, IWorkflowClient } from '../../../../types/workflow';
import type {
  IWorkflowsList,
  TOpenWorkflowLogPopupPayload,
  TRemoveWorkflowFromListPayload,
} from '../../../../redux/workflows/types';
import type { IWorkflowsFiltersProps } from '../../types';
import type { EColumnWidthMinWidth } from './Columns/Cells/WorkflowTableConstants';

export type TTableColumns = {
  'system-column-workflow': IWorkflowClient;
  'system-column-templateName': IWorkflowClient;
  'system-column-starter': IWorkflowClient;
  'system-column-progress': IWorkflowClient;
  'system-column-step': IWorkflowClient;
  'system-column-performer': IWorkflowClient;
} & {
  [key: string]: ITableViewFields;
};

export type TWorkflowColumn = Column<TTableColumns> & {
  columnType: keyof typeof EColumnWidthMinWidth;
};

export type TCustomHeaderGroup<T extends object> = HeaderGroup<T> & {
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

export interface ITableViewContainerRef {
  element: HTMLDivElement | null;
}

export interface ITableViewContainerProps {
  children: ReactNode;
}

export interface IWorkflowsTableGridProps {
  table: TableInstance<TTableColumns>;
  tableRef: RefObject<HTMLTableElement>;
  tableHeight: number;
  columns: Column<TTableColumns>[];
  colWidths: Record<string, number>;
  handleMouseDown(event: MouseEvent, columnId: string, minWidth: number): void;
  itemsCount: number;
  shouldSkeletonBody: boolean;
  shouldSkeletonDefaultTable: boolean;
  shouldSkeletonOptionalTable: boolean;
}

export interface IWorkflowsTableActionsProps {
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  isWideTable?: boolean;
  isMobile?: boolean;
}
