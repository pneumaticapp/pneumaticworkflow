import { EWorkflowStatus } from '../../../types/workflow';
import { getDueInData } from '../../DueIn/utils/getDueInData';
import { EProgressbarColor } from '../../ProgressBar';

export function getWorkflowProgressColor(
  workflowStatus: EWorkflowStatus,
  dueDates: (string | null)[],
  locale?: string,
) {
  const isOverdue = getDueInData(dueDates, undefined, undefined, locale)?.isOverdue || false;

  const colorStatusMap = [
    {
      check: () => workflowStatus === EWorkflowStatus.Running && !isOverdue,
      color: EProgressbarColor.Yellow,
    },
    {
      check: () => workflowStatus === EWorkflowStatus.Running && isOverdue,
      color: EProgressbarColor.Red,
    },
    {
      check: () => workflowStatus === EWorkflowStatus.Snoozed,
      color: EProgressbarColor.Grey,
    },
    {
      check: () => workflowStatus === EWorkflowStatus.Finished,
      color: EProgressbarColor.Green,
    },
  ];

  const progressColor = colorStatusMap.find(({ check }) => check())?.color || EProgressbarColor.Yellow;

  return progressColor;
}
