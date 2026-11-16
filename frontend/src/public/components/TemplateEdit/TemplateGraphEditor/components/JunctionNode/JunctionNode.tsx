import * as React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useIntl } from 'react-intl';

import { IJunctionNodeData } from '../../types';
import { isCheckIfJunctionId } from '../../utils/graphConstants';
import styles from './JunctionNode.css';

const JUNCTION_HANDLE_STYLE: React.CSSProperties = {
  top: '50%',
  left: '50%',
  right: 'auto',
  bottom: 'auto',
  width: 1,
  height: 1,
  minWidth: 0,
  minHeight: 0,
  background: 'transparent',
  border: 'none',
  opacity: 0,
  pointerEvents: 'none',
  transform: 'translate(-50%, -50%)',
};

const JUNCTION_HANDLES: { id: string; type: 'source' | 'target'; position: Position }[] = [
  { id: 'target-top', type: 'target', position: Position.Top },
  { id: 'target-left', type: 'target', position: Position.Left },
  { id: 'target-right', type: 'target', position: Position.Right },
  { id: 'target-bottom', type: 'target', position: Position.Bottom },
  { id: 'source-top', type: 'source', position: Position.Top },
  { id: 'source-bottom', type: 'source', position: Position.Bottom },
  { id: 'source-left', type: 'source', position: Position.Left },
  { id: 'source-right', type: 'source', position: Position.Right },
];

export const JunctionNode = ({ id, data }: NodeProps<IJunctionNodeData>) => {
  const { formatMessage } = useIntl();
  const labelId = data.kind === 'fork' ? 'template.graph-fork' : 'template.graph-join';
  let nodeClassName = styles['junction-node'];

  if (isCheckIfJunctionId(id)) {
    nodeClassName = `${styles['junction-node']} ${styles['junction-node--check-if']}`;
  }

  return (
    <div
      className={nodeClassName}
      data-test-id="graph-junction-node"
      data-kind={data.kind}
      aria-label={formatMessage({ id: labelId })}
    >
      {JUNCTION_HANDLES.map(({ id: handleId, type, position }) => (
        <Handle
          key={handleId}
          type={type}
          position={position}
          id={handleId}
          isConnectable={false}
          className={styles['junction-node__handle']}
          style={JUNCTION_HANDLE_STYLE}
        />
      ))}
    </div>
  );
};
