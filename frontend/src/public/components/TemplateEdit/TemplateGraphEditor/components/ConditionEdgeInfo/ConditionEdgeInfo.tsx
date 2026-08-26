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
  clauses,
}: IConditionEdgeInfoProps): React.ReactElement => {
  const { formatMessage } = useIntl();
  const className = [styles['edge-info'], styles['edge-info--conditional'], 'nodrag', 'nopan'].join(' ');
  const fromClauses = (clauses ?? [])
    .map((clause, index) => {
      const text = formatClause(clause, formatMessage);

      if (index === 0) {
        return text;
      }

      return `${clause.logicOperation ?? 'and'} ${text}`;
    })
    .join(' ');
  const predicate = fromClauses || summary || formatMessage({ id: 'template.graph-edge-condition' });
  const content = formatMessage({ id: 'template.graph-edge-if' }, { summary: predicate });

  const icon = (
    <span className={className} data-test-id="graph-edge-info">
      <FilledInfoIcon fill="var(--pneumatic-color-link)" width={20} height={20} />
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
