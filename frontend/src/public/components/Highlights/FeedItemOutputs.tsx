import React from 'react';

import { EExtraFieldType, IExtraField } from '../../types/template';
import { EWorkflowLogEvent } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../KickoffOutputs';

import { Ellipsis } from './Ellipsis';
import { IFeedItemOutputsProps } from './types';

export function FeedItemOutputs({ kickoff, isTextExpanded, onExpand, task, type }: IFeedItemOutputsProps) {
  if (!task) {
    return null;
  }

  const outputsByEvent: { [key in EWorkflowLogEvent]?: IExtraField[] } = {
    [EWorkflowLogEvent.WorkflowRun]: kickoff?.output,
    [EWorkflowLogEvent.WorkflowComplete]: task.output,
    [EWorkflowLogEvent.TaskComplete]: task.output,
    [EWorkflowLogEvent.WorkflowsReturned]: task.output,
    [EWorkflowLogEvent.TaskRevert]: task.output,
  };
  const outputs = outputsByEvent[type];

  if (!outputs || !isArrayWithItems(outputs)) {
    return null;
  }

  const filteredOutputs = outputs.filter((output) => {
    const value = output.type === EExtraFieldType.User ? output.userId || output.groupId : output.value;
    const hasFileValue = output.type === EExtraFieldType.File && Boolean(output.markdownValue);

    return value || output.attachments?.length || hasFileValue;
  });

  return (
    <>
      <KickoffOutputs
        outputs={filteredOutputs}
        viewMode={EKickoffOutputsViewModes.Short}
        isTruncated={!isTextExpanded}
      />
      {filteredOutputs.length > 1 && !isTextExpanded && <Ellipsis expand={onExpand} />}
    </>
  );
}
