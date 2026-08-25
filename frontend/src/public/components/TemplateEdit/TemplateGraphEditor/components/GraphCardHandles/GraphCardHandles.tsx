import * as React from 'react';
import { Handle, Position } from 'reactflow';

import { IConnectedHandles } from '../../types';
import { graphNodeHandleClassName } from '../GraphNodeCard/GraphNodeCard';
import cardStyles from '../GraphNodeCard/GraphNodeCard.css';

interface IGraphCardHandlesProps {
  handles: IConnectedHandles;
  includeTargets: boolean;
}

interface IHandleSpec {
  id: string;
  type: 'source' | 'target';
  position: Position;
  flag: keyof IConnectedHandles;
}

const SOURCE_HANDLES: IHandleSpec[] = [
  { id: 'source-top', type: 'source', position: Position.Top, flag: 'hasSourceTop' },
  { id: 'source-bottom', type: 'source', position: Position.Bottom, flag: 'hasSourceBottom' },
  { id: 'source-left', type: 'source', position: Position.Left, flag: 'hasSourceLeft' },
  { id: 'source-right', type: 'source', position: Position.Right, flag: 'hasSourceRight' },
];

const TARGET_HANDLES: IHandleSpec[] = [
  { id: 'target-top', type: 'target', position: Position.Top, flag: 'hasTargetTop' },
  { id: 'target-bottom', type: 'target', position: Position.Bottom, flag: 'hasTargetBottom' },
  { id: 'target-left', type: 'target', position: Position.Left, flag: 'hasTargetLeft' },
  { id: 'target-right', type: 'target', position: Position.Right, flag: 'hasTargetRight' },
];

function handleClassName(isConnected: boolean): string {
  return isConnected
    ? graphNodeHandleClassName
    : `${graphNodeHandleClassName} ${cardStyles['graph-node-card__handle--idle']}`;
}

export const GraphCardHandles = ({ handles, includeTargets }: IGraphCardHandlesProps) => (
  <>
    {SOURCE_HANDLES.map(({ id, type, position, flag }) => (
      <Handle
        key={id}
        type={type}
        position={position}
        id={id}
        isConnectable={false}
        className={handleClassName(handles[flag])}
      />
    ))}
    {includeTargets && TARGET_HANDLES.map(({ id, type, position, flag }) => (
      <Handle
        key={id}
        type={type}
        position={position}
        id={id}
        isConnectable={false}
        className={handleClassName(handles[flag])}
      />
    ))}
  </>
);
