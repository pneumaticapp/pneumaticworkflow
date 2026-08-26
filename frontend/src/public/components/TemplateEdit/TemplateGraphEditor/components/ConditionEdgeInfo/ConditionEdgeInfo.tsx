import * as React from 'react';
import { useIntl } from 'react-intl';

import { FilledInfoIcon } from '../../../../icons';
import { Tooltip } from '../../../../UI';
import { IGraphConditionClause } from '../../types';
import { labelByOperatorMap } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { KICKOFF_START_AFTER } from '../../utils/graphConstants';
import styles from './ConditionEdgeInfo.css';

export interface IConditionEdgeInfoProps {
  summary?: string;
  startAfter?: string[];
  isConditional?: boolean;
  clauses?: IGraphConditionClause[];
}

function formatClause(
  clause: IGraphConditionClause,
  formatMessage: ReturnType<typeof useIntl>['formatMessage'],
): string {
  const fieldLabel = clause.fieldLabel === KICKOFF_START_AFTER
    ? formatMessage({ id: 'template.kick-off-form-title' })
    : clause.fieldLabel;
  let operatorLabel = '';

  if (clause.operator) {
    operatorLabel = formatMessage({ id: labelByOperatorMap[clause.operator] });
  }

  const value = clause.value ? ` ${clause.value}` : '';

  return [fieldLabel, operatorLabel].filter(Boolean).join(' ') + value;
}

export const ConditionEdgeInfo = ({
  summary,
  startAfter,
  isConditional = false,
  clauses,
}: IConditionEdgeInfoProps): React.ReactElement => {
  const { formatMessage } = useIntl();
  const className = [
    styles['edge-info'],
    isConditional ? styles['edge-info--conditional'] : '',
    'nodrag',
    'nopan',
  ]
    .filter(Boolean)
    .join(' ');
  const fromClauses = (clauses ?? [])
    .map((clause, index) => {
      const text = formatClause(clause, formatMessage);

      if (index === 0) {
        return text;
      }

      return `${clause.logicOperation ?? 'and'} ${text}`;
    })
    .join(' ');
  const startAfterLabel = (startAfter ?? [])
    .map((item) => (
      item === KICKOFF_START_AFTER
        ? formatMessage({ id: 'template.kick-off-form-title' })
        : item
    ))
    .join(', ');
  const predicate = fromClauses || summary || formatMessage({ id: 'template.graph-edge-condition' });
  let content = formatMessage({ id: 'template.graph-edge-start-after' }, { summary: startAfterLabel });
  let fill = 'var(--pneumatic-color-black16)';

  if (isConditional) {
    content = formatMessage({ id: 'template.graph-edge-if' }, { summary: predicate });
    fill = 'var(--pneumatic-color-link)';
  }

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
