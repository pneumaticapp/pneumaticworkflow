import { Dispatch, SetStateAction, useEffect, useMemo, useState } from 'react';
import { Column } from 'react-table';

import { EWorkflowsLoadingStatus } from '../../../../../types/workflow';
import { getPerformersAvatarsWidth } from '../../../../WorkflowCardUsers/utils/getPerformersAvatarsWidth';
import { ETableViewFieldsWidth } from '../Columns/Cells/WorkflowTableConstants';
import { TableColumns } from '../types';
import { createResizeHandler } from '../utils/resizeUtils';

type TUseSavedColumnWidthsParams = {
  currentUserId?: number;
  templateId?: number;
  maxPerformersCount: number;
};

type TUseColumnWidthsParams = {
  columns: Column<TableColumns>[];
  workflowsLoadingStatus: EWorkflowsLoadingStatus;
  currentUserId?: number;
  templateId?: number;
};

const readWidths = (key: string): Record<string, number> =>
  JSON.parse(localStorage.getItem(key) || '{}');

export function useSavedColumnWidths({
  currentUserId,
  templateId,
  maxPerformersCount,
}: TUseSavedColumnWidthsParams) {
  const savedGlobalWidths = useMemo(
    () => readWidths(`workflow-column-widths-${currentUserId}-global`),
    [currentUserId],
  );
  const savedOptionalWidths = useMemo(
    () => readWidths(`workflow-column-widths-${currentUserId}-template-${templateId}`),
    [currentUserId, templateId],
  );
  const performerColumnMinWidth = getPerformersAvatarsWidth(maxPerformersCount);
  const performerColumnWidth = Math.max(
    savedGlobalWidths['system-column-performer']
      || ETableViewFieldsWidth['system-column-performer'],
    performerColumnMinWidth,
  );

  return {
    savedGlobalWidths,
    savedOptionalWidths,
    performerColumnMinWidth,
    performerColumnWidth,
  };
}

export function mergeColumnWidths(
  previousWidths: Record<string, number>,
  columns: Column<TableColumns>[],
): Record<string, number> {
  const nextWidths = { ...previousWidths };

  columns.forEach((column) => {
    const id = column.accessor as string;
    const width = column.width as number;

    nextWidths[id] = id === 'system-column-performer' && nextWidths[id]
      ? Math.max(nextWidths[id], width)
      : nextWidths[id] || width;
  });

  return nextWidths;
}

export function useWorkflowColumnWidths({
  columns,
  workflowsLoadingStatus,
  currentUserId,
  templateId,
}: TUseColumnWidthsParams): {
  colWidths: Record<string, number>;
  setColWidths: Dispatch<SetStateAction<Record<string, number>>>;
  handleMouseDown: ReturnType<typeof createResizeHandler>;
} {
  const [colWidths, setColWidths] = useState<Record<string, number>>({});

  useEffect(() => {
    if (
      workflowsLoadingStatus !== EWorkflowsLoadingStatus.Loaded
      && workflowsLoadingStatus !== EWorkflowsLoadingStatus.LoadingNextPage
    ) {
      return;
    }

    setColWidths((previousWidths) => mergeColumnWidths(previousWidths, columns));
  }, [columns, workflowsLoadingStatus]);

  return {
    colWidths,
    setColWidths,
    handleMouseDown: createResizeHandler(
      colWidths,
      setColWidths,
      currentUserId,
      templateId,
    ),
  };
}
