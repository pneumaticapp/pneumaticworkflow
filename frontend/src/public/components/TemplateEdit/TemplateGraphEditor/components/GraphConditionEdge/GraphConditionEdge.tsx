import * as React from 'react';
import { EdgeLabelRenderer, EdgeProps } from 'reactflow';

import { IConditionEdgeData } from '../../types';
import { getGraphEdgePath } from '../../utils/getGraphEdgePath';
import { ConditionEdgeInfo } from '../ConditionEdgeInfo/ConditionEdgeInfo';
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
    sourcePosition,
    targetPosition,
  });
  const isConditional = Boolean(data?.isConditional);
  const hasInfo = Boolean(data?.summary) || Boolean(data?.startAfter?.length);
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
        style={style}
        markerEnd={markerEnd}
      />
      {hasInfo && (
        <EdgeLabelRenderer>
          <div
            className={labelClassName}
            style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}
            data-test-id="graph-edge-label"
          >
            <ConditionEdgeInfo
              summary={data?.summary}
              startAfter={data?.startAfter}
              isConditional={isConditional}
            />
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};
