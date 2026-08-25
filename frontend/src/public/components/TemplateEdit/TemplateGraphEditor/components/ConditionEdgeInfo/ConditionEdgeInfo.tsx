import * as React from 'react';
import { useIntl } from 'react-intl';

import { FilledInfoIcon } from '../../../../icons';
import { Tooltip } from '../../../../UI';
import { KICKOFF_START_AFTER } from '../../utils/templateToGraph';
import styles from './ConditionEdgeInfo.css';

export interface IConditionEdgeInfoProps {
  summary?: string;
  startAfter?: string[];
  isConditional?: boolean;
}

export const ConditionEdgeInfo = ({
  summary,
  startAfter,
  isConditional = false,
}: IConditionEdgeInfoProps): React.ReactElement => {
  const { formatMessage } = useIntl();
  const fill = isConditional ? 'var(--pneumatic-color-link)' : 'var(--pneumatic-color-black16)';
  const className = [
    styles['edge-info'],
    isConditional ? styles['edge-info--conditional'] : '',
    'nodrag',
    'nopan',
  ]
    .filter(Boolean)
    .join(' ');

  const startAfterLabel = (startAfter ?? [])
    .map((item) => (
      item === KICKOFF_START_AFTER ? formatMessage({ id: 'template.kick-off-form-title' }) : item
    ))
    .join(', ');
  const content = isConditional
    ? formatMessage(
      { id: 'template.graph-edge-if' },
      { summary: summary || formatMessage({ id: 'template.graph-edge-condition' }) },
    )
    : formatMessage({ id: 'template.graph-edge-start-after' }, { summary: startAfterLabel });

  const icon = (
    <span className={className} data-test-id="graph-edge-info">
      <FilledInfoIcon fill={fill} width={20} height={20} />
    </span>
  );

  return (
    <Tooltip
      content={content}
      size="md"
      placement="top"
      appendTo={() => document.body}
      zIndex={1100}
      interactive={false}
      maxWidth="19.2rem"
      className={styles['tooltip-box']}
      contentClassName={styles['tooltip-content']}
    >
      {icon}
    </Tooltip>
  );
};
