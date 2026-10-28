import * as React from 'react';
import classnames from 'classnames';

import { ClearIcon, ExpandIcon } from '../../icons';
import type { IControlSMParams } from './types';

import styles from './Select.css';

export function ControlSM(props: any) {
  const { title, isOpen, isDisabled, variant, className, Icon, content, onToggle, onClear }: IControlSMParams =
    props.selectProps.controlSm;

  if (content) {
    return (
      <button
        ref={props.innerRef}
        type="button"
        disabled={isDisabled}
        className={classnames(styles['select-sm__control-custom'], className)}
        onClick={() => onToggle(!isOpen)}
      >
        {content}
      </button>
    );
  }

  return (
    <button
      ref={props.innerRef}
      type="button"
      disabled={isDisabled}
      className={classnames(
        styles['select-sm__control'],
        variant === 'accent' && styles['select-sm__control_accent'],
        isOpen && styles['is-open'],
        className,
      )}
      onClick={() => onToggle(!isOpen)}
    >
      {Icon && <Icon className={styles['select-sm__icon']} />}
      <p className={styles['select-sm__value']}>{title || props?.selectProps.value?.label}</p>
      {onClear ? (
        <span
          role="button"
          tabIndex={0}
          aria-label="Clear selected options"
          className={styles['select-sm__clear-value']}
          onClick={(event) => {
            event.stopPropagation();
            onClear();
          }}
          onKeyDown={(event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            event.preventDefault();
            event.stopPropagation();
            onClear();
          }}
        >
          <ClearIcon />
        </span>
      ) : (
        <ExpandIcon className={classnames(styles['select-sm__arrow'], isOpen && styles['is-open'])} />
      )}
    </button>
  );
}
