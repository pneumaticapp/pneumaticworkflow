import * as React from 'react';
import { EdgeLabelRenderer, EdgeProps } from 'reactflow';

import { IConditionEdgeData } from '../../types';
import { getGraphEdgePath } from '../../utils/getGraphEdgePath';
import { ConditionEdgeInfo } from '../ConditionEdgeInfo/ConditionEdgeInfo';
import { GraphAddTaskButton } from '../GraphAddTaskButton/GraphAddTaskButton';
import styles from './GraphConditionEdge.css';

export const GraphConditionEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  sourceHandleId,
  targetHandleId,
  style,
  data,
  markerEnd,
}: EdgeProps<IConditionEdgeData>) => {
  const { path: edgePath, labelX, labelY } = getGraphEdgePath({
    sourceX: data?.sourceAnchor?.x ?? sourceX,
    sourceY: data?.sourceAnchor?.y ?? sourceY,
    targetX: data?.targetAnchor?.x ?? targetX,
    targetY: data?.targetAnchor?.y ?? targetY,
    pathKind: data?.pathKind,
    laneX: data?.laneX,
    laneY: data?.laneY,
    sourceHandle: data?.sourceHandle ?? sourceHandleId,
    targetHandle: data?.targetHandle ?? targetHandleId,
    sourceStandoff: data?.sourceStandoff,
    targetStandoff: data?.targetStandoff,
    sourcePosition,
    targetPosition,
  });
  const hasCheckIfInfo = Boolean(data?.isConditional && (data.summary || data.clauses?.length));
  const hasStartAfterInfo = Boolean(!data?.isConditional && data?.startAfter?.length);
  const hasInfo = hasCheckIfInfo || hasStartAfterInfo;
  const addTaskIntent = data?.addTaskIntent;
  const onAddTask = data?.onAddTask;
  const showAddTask = Boolean(addTaskIntent && onAddTask);
  const showLabel = hasInfo || showAddTask;
  const labelClassName = [
    styles['edge-label'],
    data?.focus === 'dimmed' ? styles['edge-label--dimmed'] : '',
    'nodrag',
    'nopan',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        fill="none"
        style={{ ...style, pointerEvents: 'none' }}
        markerEnd={markerEnd}
      />
      {showLabel && (
        <EdgeLabelRenderer>
          <div
            className={labelClassName}
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
            data-test-id="graph-edge-label"
          >
            <div className={styles['edge-label__row']}>
              {hasInfo && (
                <ConditionEdgeInfo
                  summary={data?.summary}
                  startAfter={data?.startAfter}
                  isConditional={Boolean(data?.isConditional)}
                  clauses={data?.clauses}
                />
              )}
              {showAddTask && addTaskIntent && onAddTask && (
                <GraphAddTaskButton intent={addTaskIntent} onAddTask={onAddTask} />
              )}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};
