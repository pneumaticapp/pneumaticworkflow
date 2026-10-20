import * as React from 'react';
import { useCallback, useEffect } from 'react';
import { NodeProps, useUpdateNodeInternals } from 'reactflow';
import { useIntl } from 'react-intl';

import { ITaskNodeData } from '../../types';
import { EMPTY_CONNECTED_HANDLES } from '../../utils/applyConnectedHandles';
import { countCheckIfConditions } from '../../utils/countCheckIfConditions';
import { GraphAddTaskButton } from '../GraphAddTaskButton/GraphAddTaskButton';
import { GraphCardHandles } from '../GraphCardHandles/GraphCardHandles';
import { GraphNodeCard } from '../GraphNodeCard/GraphNodeCard';
import { GraphTaskCardDropdown } from '../GraphTaskCardDropdown/GraphTaskCardDropdown';
import cardStyles from '../GraphNodeCard/GraphNodeCard.css';

export const TaskNode = ({ id, data, selected }: NodeProps<ITaskNodeData>) => {
  const { formatMessage } = useIntl();
  const updateNodeInternals = useUpdateNodeInternals();
  const { task, onEdit, onDelete, handles = EMPTY_CONNECTED_HANDLES, addTaskIntent, onAddTask } = data;
  const performersCount = task.rawPerformers?.length ?? 0;
  const conditionsCount = countCheckIfConditions(task.conditions);
  const fieldsCount = task.fields?.length ?? 0;

  const connectedSignature = [
    handles.hasSourceTop,
    handles.hasSourceBottom,
    handles.hasSourceLeft,
    handles.hasSourceRight,
    handles.hasTargetTop,
    handles.hasTargetBottom,
    handles.hasTargetLeft,
    handles.hasTargetRight,
  ].join('');

  useEffect(() => {
    updateNodeInternals(id);
  }, [id, connectedSignature, updateNodeInternals]);

  const handleEdit = useCallback(() => {
    onEdit(task.apiName);
  }, [task.apiName, onEdit]);

  const handleDelete = useCallback(() => {
    onDelete(task.apiName);
  }, [task.apiName, onDelete]);

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
        <span
          className={`${cardStyles['graph-node-card__meta-item']} ${cardStyles['graph-node-card__meta-item--accent']}`}
        >
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
      menu={<GraphTaskCardDropdown onEdit={handleEdit} onDelete={handleDelete} />}
      meta={meta}
      handles={<GraphCardHandles handles={handles} includeTargets />}
      addTask={addTaskIntent && onAddTask ? <GraphAddTaskButton intent={addTaskIntent} onAddTask={onAddTask} /> : null}
    />
  );
};
