import * as React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useIntl } from 'react-intl';

import { IJunctionNodeData } from '../../types';
import styles from './JunctionNode.css';

export const JunctionNode = ({ data }: NodeProps<IJunctionNodeData>) => {
  const { formatMessage } = useIntl();
  const labelId = data.kind === 'fork' ? 'template.graph-fork' : 'template.graph-join';

  return (
    <div
      className={styles['junction-node']}
      data-test-id="graph-junction-node"
      data-kind={data.kind}
      aria-label={formatMessage({ id: labelId })}
    >
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        isConnectable={false}
        className={styles['junction-node__handle']}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="source-bottom"
        isConnectable={false}
        className={styles['junction-node__handle']}
      />
    </div>
  );
};
