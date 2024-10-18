import * as React from 'react';
import { CellProps } from 'react-table';
import { useSelector } from 'react-redux';
import { getLanguage } from '../../../../../../../redux/selectors/user';
import { ProgressBar } from '../../../../../../ProgressBar';
import { getWorkflowProgress } from '../../../../../utils/getWorkflowProgress';
import { getWorkflowProgressColor } from '../../../../../utils/getWorkflowProgressColor';
import { ProgressbarTooltipContents } from '../../../../../utils/ProgressbarTooltipContents';

import { TableColumns } from '../../../types';

type TProps = React.PropsWithChildren<CellProps<TableColumns, TableColumns['workflow']>>;

export function ProgressColumn({ value: workflow }: TProps) {
  const { currentTask, tasksCount, status, task } = workflow;
  const progress = getWorkflowProgress({ currentTask, tasksCount, status });
  const locale = useSelector(getLanguage);
  const color = getWorkflowProgressColor(status, [task.dueDate, workflow.dueDate], locale);

  return (
    <ProgressBar
      progress={progress}
      color={color}
      background="#f6f6f6"
      tooltipContent={<ProgressbarTooltipContents workflow={workflow} />}
    />
  );
}
