import * as React from 'react';

import { MoreIcon } from '../../../../icons';
import styles from './GraphNodeCard.css';

export const graphNodeHandleClassName = styles['graph-node-card__handle'];

interface IGraphNodeCardProps {
  label: string;
  title: string;
  meta?: React.ReactNode;
  isSelected?: boolean;
  onClick?: () => void;
  onEdit?: () => void;
  editLabel?: string;
  handles?: React.ReactNode;
  addTask?: React.ReactNode;
  testId?: string;
}

export const GraphNodeCard = ({
  label,
  title,
  meta,
  isSelected,
  onClick,
  onEdit,
  editLabel,
  handles,
  addTask,
  testId,
}: IGraphNodeCardProps) => {
  const className = isSelected
    ? `${styles['graph-node-card']} ${styles['graph-node-card--selected']}`
    : styles['graph-node-card'];

  return (
    <div
      className={className}
      data-test-id={testId}
      data-selected={isSelected ? 'true' : undefined}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (!onClick) {
          return;
        }

        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onClick();
        }
      }}
    >
      {handles}
      <div className={styles['graph-node-card__header']}>
        <span className={styles['graph-node-card__label']}>{label}</span>
        {onEdit ? (
          <button
            type="button"
            className={`${styles['graph-node-card__kebab']} nodrag nopan`}
            aria-label={editLabel}
            data-test-id="graph-node-edit"
            onClick={(event) => {
              event.stopPropagation();
              onEdit();
            }}
          >
            <MoreIcon fill="currentColor" />
          </button>
        ) : (
          <span className={styles['graph-node-card__kebab']} aria-hidden="true">
            <MoreIcon fill="currentColor" />
          </span>
        )}
      </div>
      <div className={styles['graph-node-card__title']}>{title}</div>
      {meta}
      {addTask && (
        <div className={styles['graph-node-card__add']}>
          {addTask}
        </div>
      )}
    </div>
  );
};
