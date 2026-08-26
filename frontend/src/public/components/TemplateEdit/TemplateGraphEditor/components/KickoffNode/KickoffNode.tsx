import * as React from 'react';
import { useEffect } from 'react';
import { NodeProps, useUpdateNodeInternals } from 'reactflow';
import { useIntl } from 'react-intl';

import { IKickoffNodeData } from '../../types';
import { EMPTY_CONNECTED_HANDLES } from '../../utils/applyConnectedHandles';
import { getPlainText } from '../../utils/getPlainText';
import { GraphAddTaskButton } from '../GraphAddTaskButton/GraphAddTaskButton';
import { GraphCardHandles } from '../GraphCardHandles/GraphCardHandles';
import { GraphNodeCard } from '../GraphNodeCard/GraphNodeCard';
import cardStyles from '../GraphNodeCard/GraphNodeCard.css';

export const KickoffNode = ({ id, data, selected }: NodeProps<IKickoffNodeData>) => {
  const { formatMessage } = useIntl();
  const updateNodeInternals = useUpdateNodeInternals();
  const kickoff = data?.kickoff;
  const handles = data?.handles ?? EMPTY_CONNECTED_HANDLES;
  const addTaskIntent = data?.addTaskIntent;
  const onAddTask = data?.onAddTask;
  const fieldsCount = kickoff?.fields?.length ?? 0;
  const title = getPlainText(kickoff?.description);

  const connectedSignature = [
    handles.hasSourceTop,
    handles.hasSourceBottom,
    handles.hasSourceLeft,
    handles.hasSourceRight,
  ].join('');

  useEffect(() => {
    updateNodeInternals(id);
  }, [id, connectedSignature, updateNodeInternals]);

  const meta = fieldsCount > 0 ? (
    <div className={cardStyles['graph-node-card__meta']}>
      <span className={cardStyles['graph-node-card__meta-item']}>
        {formatMessage({ id: 'template.graph-fields-count' }, { count: fieldsCount })}
      </span>
    </div>
  ) : null;

  return (
    <GraphNodeCard
      testId="graph-kickoff-node"
      label={formatMessage({ id: 'template.kick-off-form-title' })}
      title={title}
      isSelected={selected}
      onEdit={data.onEdit}
      editLabel={formatMessage({ id: 'kickoff.menu-edit' })}
      meta={meta}
      handles={(
        <GraphCardHandles handles={handles} includeTargets={false} />
      )}
      addTask={addTaskIntent && onAddTask ? (
        <GraphAddTaskButton intent={addTaskIntent} onAddTask={onAddTask} />
      ) : null}
    />
  );
};
