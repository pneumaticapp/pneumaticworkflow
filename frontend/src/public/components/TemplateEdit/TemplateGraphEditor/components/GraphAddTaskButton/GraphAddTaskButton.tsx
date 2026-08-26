import * as React from 'react';
import { useCallback } from 'react';
import { useIntl } from 'react-intl';

import { BoldPlusIcon } from '../../../../icons';
import { TGraphAddTaskIntent } from '../../types';
import styles from './GraphAddTaskButton.css';

export interface IGraphAddTaskButtonProps {
  intent: TGraphAddTaskIntent;
  onAddTask: (intent: TGraphAddTaskIntent) => void;
}

export const GraphAddTaskButton = ({ intent, onAddTask }: IGraphAddTaskButtonProps) => {
  const { formatMessage } = useIntl();

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
      className={`${styles['graph-add-task']} nodrag nopan`}
      aria-label={formatMessage({ id: 'template.graph-add-task' })}
      data-test-id="graph-add-task"
      data-kind={intent.kind}
      onClick={handleClick}
    >
      <BoldPlusIcon fill="currentColor" />
    </button>
  );
};
