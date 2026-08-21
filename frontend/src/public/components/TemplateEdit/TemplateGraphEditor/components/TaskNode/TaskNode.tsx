import * as React from 'react';
import { useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useIntl } from 'react-intl';

import { ITaskNodeData } from '../../types';
import { EMPTY_CONNECTED_HANDLES } from '../../utils/applyConnectedHandles';
import { GraphNodeCard, graphNodeHandleClassName, graphNodeSkipHandleClassName } from '../GraphNodeCard/GraphNodeCard';
import cardStyles from '../GraphNodeCard/GraphNodeCard.css';

export const TaskNode = ({ data, selected }: NodeProps<ITaskNodeData>) => {
  const { formatMessage } = useIntl();
  const { task, onEdit, handles = EMPTY_CONNECTED_HANDLES } = data;
  const performersCount = task.rawPerformers?.length ?? 0;
  const conditionsCount = task.conditions?.length ?? 0;
  const fieldsCount = task.fields?.length ?? 0;

  const handleEdit = useCallback(() => {
    onEdit(task.apiName);
  }, [task.apiName, onEdit]);

  const meta = (
    <div className={cardStyles['graph-node-card__meta']}>
      {performersCount > 0 && (
        <span className={cardStyles['graph-node-card__meta-item']}>
          {formatMessage({ id: 'template.graph-performers-count' }, { count: performersCount })}
        </span>
      )}
      {fieldsCount > 0 && (
        <span className={cardStyles['graph-node-card__meta-item']}>
          {formatMessage({ id: 'template.graph-fields-count' }, { count: fieldsCount })}
        </span>
      )}
      {conditionsCount > 0 && (
        <span className={`${cardStyles['graph-node-card__meta-item']} ${cardStyles['graph-node-card__meta-item--accent']}`}>
          {formatMessage({ id: 'template.graph-conditions-count' }, { count: conditionsCount })}
        </span>
      )}
    </div>
  );

  return (
    <GraphNodeCard
      testId="graph-task-node"
      label={`${formatMessage({ id: 'template.task' })} ${task.number}`}
      title={task.name ?? ''}
      isSelected={selected}
      onEdit={handleEdit}
      editLabel={formatMessage({ id: 'template.task-edit' })}
      meta={meta}
      handles={(
        <>
          {handles.hasTargetTop && (
            <Handle type="target" position={Position.Top} id="target-top" className={graphNodeHandleClassName} />
          )}
          {handles.hasSourceBottom && (
            <Handle type="source" position={Position.Bottom} id="source-bottom" className={graphNodeHandleClassName} />
          )}
          {handles.hasSourceSkip && (
            <Handle type="source" position={Position.Right} id="source-skip" className={graphNodeSkipHandleClassName} />
          )}
          {handles.hasTargetSkip && (
            <Handle type="target" position={Position.Left} id="target-skip" className={graphNodeSkipHandleClassName} />
          )}
        </>
      )}
    />
  );
};
