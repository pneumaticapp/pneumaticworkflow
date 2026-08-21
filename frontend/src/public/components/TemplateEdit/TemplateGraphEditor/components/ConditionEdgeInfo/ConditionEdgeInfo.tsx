import * as React from 'react';
import { useIntl } from 'react-intl';

import { InfoIcon } from '../../../../icons';
import { Tooltip } from '../../../../UI';
import styles from './ConditionEdgeInfo.css';

interface IConditionEdgeInfoProps {
  summary?: string;
  isConditional?: boolean;
}

export const ConditionEdgeInfo = ({ summary, isConditional = false }: IConditionEdgeInfoProps) => {
  const { formatMessage } = useIntl();
  const fill = isConditional ? 'var(--pneumatic-color-link)' : 'var(--pneumatic-color-black16)';
  const icon = (
    <span className={`${styles['edge-info']} nodrag nopan`} data-test-id="graph-edge-info">
      <InfoIcon fill={fill} width={20} height={20} />
    </span>
  );

  if (!summary) {
    return icon;
  }

  return (
    <Tooltip content={formatMessage({ id: 'template.graph-edge-if' }, { summary })} size="md">
      {icon}
    </Tooltip>
  );
};
