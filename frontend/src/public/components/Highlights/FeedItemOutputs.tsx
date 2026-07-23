import React from 'react';

import { EExtraFieldType, IExtraField } from '../../types/template';
import { EWorkflowLogEvent } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../KickoffOutputs';

import { Ellipsis } from './Ellipsis';
import { IFeedItemOutputsProps } from './types';

export function FeedItemOutputs({ kickoff, isTextExpanded, onExpand, task, type }: IFeedItemOutputsProps) {
  const outputsByEvent: { [key in EWorkflowLogEvent]?: IExtraField[] } = {
    [EWorkflowLogEvent.WorkflowRun]: kickoff?.output,
    [EWorkflowLogEvent.WorkflowComplete]: task?.output,
    [EWorkflowLogEvent.TaskComplete]: task?.output,
    [EWorkflowLogEvent.WorkflowsReturned]: task?.output,
    [EWorkflowLogEvent.TaskRevert]: task?.output,
  };
  const fieldsetsByEvent = {
    [EWorkflowLogEvent.WorkflowRun]: kickoff?.fieldsets,
    [EWorkflowLogEvent.WorkflowComplete]: task?.fieldsets,
    [EWorkflowLogEvent.TaskComplete]: task?.fieldsets,
    [EWorkflowLogEvent.WorkflowsReturned]: task?.fieldsets,
    [EWorkflowLogEvent.TaskRevert]: task?.fieldsets,
  };
  const outputs = outputsByEvent[type] ?? [];
  const fieldsets = fieldsetsByEvent[type as keyof typeof fieldsetsByEvent] ?? [];

  if (!isArrayWithItems(outputs) && !isArrayWithItems(fieldsets)) {
    return null;
  }

  const hasValue = (output: IExtraField) => {
    const value = output.type === EExtraFieldType.User ? output.userId || output.groupId : output.value;
    const hasFileValue = output.type === EExtraFieldType.File && Boolean(output.markdownValue);

    return value || output.attachments?.length || hasFileValue;
  };
  const filteredOutputs = outputs.filter(hasValue);
  const filteredFieldsets = fieldsets
    .map((fieldset) => ({ ...fieldset, fields: fieldset.fields.filter(hasValue) }))
    .filter((fieldset) => fieldset.fields.length > 0);

  return (
    <>
      <KickoffOutputs
        outputs={filteredOutputs}
        fieldsets={filteredFieldsets}
        viewMode={EKickoffOutputsViewModes.Short}
        isTruncated={!isTextExpanded}
      />
      {filteredOutputs.length + filteredFieldsets.flatMap((fieldset) => fieldset.fields).length > 1
        && !isTextExpanded
        && <Ellipsis expand={onExpand} />}
    </>
  );
}
