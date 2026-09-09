import * as React from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';

import { useCloseOnOutsideClick } from '../../../../../hooks/useCloseOnOutsideClick';
import { EditIcon, MoreIcon, TrashIcon } from '../../../../icons';
import styles from './GraphTaskCardDropdown.css';

export interface IGraphTaskCardDropdownProps {
  onEdit(): void;
  onDelete(): void;
}

export const GraphTaskCardDropdown = ({ onEdit, onDelete }: IGraphTaskCardDropdownProps) => {
  const { formatMessage } = useIntl();
  const rootRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);

  const close = useCallback((): void => {
    setIsOpen(false);
    setIsConfirmingDelete(false);
  }, []);

  useCloseOnOutsideClick(rootRef, close);

  useEffect(() => {
    if (!isOpen) return undefined;

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') close();
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [close, isOpen]);

  const handleToggle = useCallback((event: React.MouseEvent<HTMLButtonElement>): void => {
    event.stopPropagation();
    setIsOpen((value) => !value);
    setIsConfirmingDelete(false);
  }, []);

  const handleEdit = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>): void => {
      event.stopPropagation();
      close();
      onEdit();
    },
    [close, onEdit],
  );

  const handleRequestDelete = useCallback((event: React.MouseEvent<HTMLButtonElement>): void => {
    event.stopPropagation();
    setIsConfirmingDelete(true);
  }, []);

  const handleCancelDelete = useCallback((event: React.MouseEvent<HTMLButtonElement>): void => {
    event.stopPropagation();
    setIsConfirmingDelete(false);
  }, []);

  const handleConfirmDelete = useCallback(
    (event: React.MouseEvent<HTMLButtonElement>): void => {
      event.stopPropagation();
      close();
      onDelete();
    },
    [close, onDelete],
  );

  const handleMenuClick = useCallback((event: React.MouseEvent<HTMLDivElement>): void => {
    event.stopPropagation();
  }, []);

  const handleMenuKeyDown = useCallback((event: React.KeyboardEvent<HTMLDivElement>): void => {
    event.stopPropagation();
  }, []);

  return (
    <div ref={rootRef} className={`${styles['task-card-dropdown']} nodrag nopan`}>
      <button
        type="button"
        className={styles['task-card-dropdown__toggle']}
        aria-label={formatMessage({ id: 'template.graph-task-actions' })}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        data-test-id="graph-task-actions"
        onClick={handleToggle}
      >
        <MoreIcon fill="currentColor" />
      </button>

      {isOpen && (
        <div
          className={styles['task-card-dropdown__menu']}
          role="menu"
          tabIndex={-1}
          data-test-id="graph-task-actions-menu"
          onClick={handleMenuClick}
          onKeyDown={handleMenuKeyDown}
        >
          <button type="button" className={styles['task-card-dropdown__item']} role="menuitem" onClick={handleEdit}>
            <span>{formatMessage({ id: 'template.graph-task-edit' })}</span>
            <EditIcon />
          </button>

          <div className={styles['task-card-dropdown__divider']} />

          {isConfirmingDelete ? (
            <div className={`${styles['task-card-dropdown__item']} ${styles['task-card-dropdown__confirmation']}`}>
              <span>{formatMessage({ id: 'dropdown.are-you-sure' })}</span>
              <button type="button" className={styles['task-card-dropdown__confirm']} onClick={handleConfirmDelete}>
                {formatMessage({ id: 'dropdown.yes' })}
              </button>
              <span>/</span>
              <button type="button" className={styles['task-card-dropdown__cancel']} onClick={handleCancelDelete}>
                {formatMessage({ id: 'dropdown.no' })}
              </button>
            </div>
          ) : (
            <button
              type="button"
              className={`${styles['task-card-dropdown__item']} ${styles['task-card-dropdown__delete']}`}
              role="menuitem"
              onClick={handleRequestDelete}
            >
              <span>{formatMessage({ id: 'template.task-remove' })}</span>
              <TrashIcon />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
