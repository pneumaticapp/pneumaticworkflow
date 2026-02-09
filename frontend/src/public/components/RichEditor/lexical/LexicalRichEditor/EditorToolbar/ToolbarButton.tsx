import React, { forwardRef, useCallback, useRef } from 'react';
import classnames from 'classnames';
import { CustomTooltip } from '../../../../UI';
import type { IToolbarButtonProps } from './types';

import styles from './EditorToolbar.css';

function setRef<T>(ref: React.Ref<T> | undefined, node: T | null): void {
  if (!ref) return;
  if (typeof ref === 'function') ref(node);
  else (ref as React.MutableRefObject<T | null>).current = node;
}

export const ToolbarButton = forwardRef<HTMLButtonElement, IToolbarButtonProps>(
  function ToolbarButton(
    { isActive, tooltipText, ariaLabel, isModal, onMouseDown, children },
    ref,
  ): React.ReactElement {
    const buttonRef = useRef<HTMLButtonElement>(null);
    const handleRef = useCallback(
      (node: HTMLButtonElement | null) => {
        (buttonRef as React.MutableRefObject<HTMLButtonElement | null>).current = node;
        setRef(ref, node);
      },
      [ref],
    );

    return (
      <div className={styles['button-wrapper']}>
        <CustomTooltip
          target={buttonRef}
          tooltipText={tooltipText}
          isModal={isModal}
        />
        <button
          ref={handleRef}
          type="button"
          className={classnames(styles['button'], isActive && styles['is-active'])}
          onMouseDown={onMouseDown}
          aria-label={ariaLabel}
        >
          {children}
        </button>
      </div>
    );
  },
);
