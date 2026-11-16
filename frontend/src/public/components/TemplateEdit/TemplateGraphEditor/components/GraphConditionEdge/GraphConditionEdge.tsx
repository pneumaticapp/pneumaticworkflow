import * as React from 'react';
import { useCallback, useState } from 'react';
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
  const {
    path: edgePath,
    centerX,
    centerY,
  } = getGraphEdgePath({
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
  const hasInfo = Boolean(data?.isConditional && (data.summary || data.clauses?.length));
  const addTaskIntent = data?.addTaskIntent;
  const onAddTask = data?.onAddTask;
  const showAddTask = Boolean(addTaskIntent && onAddTask);
  const [isLineHovered, setIsLineHovered] = useState(false);
  const handleLineEnter = useCallback(() => setIsLineHovered(true), []);
  const handleLineLeave = useCallback(() => setIsLineHovered(false), []);
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
      {showAddTask && (
        <path
          className={styles['edge-hit-area']}
          d={edgePath}
          fill="none"
          onMouseEnter={handleLineEnter}
          onMouseLeave={handleLineLeave}
          data-test-id="graph-edge-hit-area"
        />
      )}
      {hasInfo && (
        <EdgeLabelRenderer>
          <div
            className={labelClassName}
            style={{ transform: `translate(-50%, -50%) translate(${centerX}px, ${centerY}px)` }}
            data-test-id="graph-edge-label"
          >
            <ConditionEdgeInfo summary={data?.summary} clauses={data?.clauses} />
          </div>
        </EdgeLabelRenderer>
      )}
      {showAddTask && addTaskIntent && onAddTask && (
        <EdgeLabelRenderer>
          <div
            className={labelClassName}
            style={{ transform: `translate(-50%, -50%) translate(${centerX}px, ${centerY}px)` }}
            data-test-id="graph-edge-add-task"
          >
            <GraphAddTaskButton intent={addTaskIntent} onAddTask={onAddTask} isHighlighted={isLineHovered} />
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};
