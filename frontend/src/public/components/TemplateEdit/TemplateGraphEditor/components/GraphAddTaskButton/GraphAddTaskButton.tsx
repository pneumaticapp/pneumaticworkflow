import * as React from 'react';
import { useCallback } from 'react';
import { useIntl } from 'react-intl';

import { PlusCircleIcon } from '../../../../icons';
import { TGraphAddTaskIntent } from '../../types';
import styles from './GraphAddTaskButton.css';

export interface IGraphAddTaskButtonProps {
  intent: TGraphAddTaskIntent;
  onAddTask: (intent: TGraphAddTaskIntent) => void;
  /** Darkens the plus while the line it sits on is highlighted. */
  isHighlighted?: boolean;
}

export const GraphAddTaskButton = ({ intent, onAddTask, isHighlighted = false }: IGraphAddTaskButtonProps) => {
  const { formatMessage } = useIntl();
  const className = [
    styles['graph-add-task'],
    isHighlighted ? styles['graph-add-task--highlighted'] : '',
    'nodrag',
    'nopan',
  ]
    .filter(Boolean)
    .join(' ');

  const handleClick = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>) => {
      event.preventDefault();
      event.stopPropagation();
      onAddTask(intent);
    },
    [intent, onAddTask],
  );

  return (
    <button
      type="button"
      className={className}
      aria-label={formatMessage({ id: 'template.graph-add-task' })}
      data-test-id="graph-add-task"
      data-kind={intent.kind}
      onClick={handleClick}
    >
      <PlusCircleIcon fill="currentColor" />
    </button>
  );
};
