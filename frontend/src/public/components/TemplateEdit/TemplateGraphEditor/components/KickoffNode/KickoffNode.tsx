import * as React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useIntl } from 'react-intl';

import { IKickoffNodeData } from '../../types';
import { EMPTY_CONNECTED_HANDLES } from '../../utils/applyConnectedHandles';
import { getPlainText } from '../../utils/getPlainText';
import { GraphNodeCard, graphNodeHandleClassName, graphNodeSkipHandleClassName } from '../GraphNodeCard/GraphNodeCard';
import cardStyles from '../GraphNodeCard/GraphNodeCard.css';

export const KickoffNode = ({ data, selected }: NodeProps<IKickoffNodeData>) => {
  const { formatMessage } = useIntl();
  const kickoff = data?.kickoff;
  const handles = data?.handles ?? EMPTY_CONNECTED_HANDLES;
  const fieldsCount = kickoff?.fields?.length ?? 0;
  const title = getPlainText(kickoff?.description);

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
        <>
          {handles.hasSourceBottom && (
            <Handle type="source" position={Position.Bottom} id="source-bottom" className={graphNodeHandleClassName} />
          )}
          {handles.hasSourceSkip && (
            <Handle type="source" position={Position.Right} id="source-skip" className={graphNodeSkipHandleClassName} />
          )}
        </>
      )}
    />
  );
};
