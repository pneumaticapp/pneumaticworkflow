import * as React from 'react';
import { useEffect, useRef } from 'react';
import classnames from 'classnames';
import { FieldHookConfig, useField } from 'formik';

import { TCheckboxProps, TCheckboxTriState } from './types';

import styles from './Checkbox.css';
import commonStyles from '../common/styles.css';

// A checkbox can be controlled either with "checked" or "triState" prop.
// The difference is that the triState prop provides an indeterminate checkbox state.

export function Checkbox({
  title,
  titlePosition,
  isRequired,
  containerClassName,
  labelClassName,
  titleClassName,
  checked,
  disabled,
  readOnly,
  onClick,
  triState,
  checkboxId,
  ...props
}: TCheckboxProps) {
  const checkboxRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!triState || !checkboxRef.current) return;

    const handleUpdateCheckboxTriState = (checkbox: HTMLInputElement) => {
      const syncMap: { [key in TCheckboxTriState]: () => void } = {
        checked: () => {
          checkbox.checked = true;
          checkbox.indeterminate = false;
        },
        empty: () => {
          checkbox.checked = false;
          checkbox.indeterminate = false;
        },
        indeterminate: () => {
          checkbox.checked = false;
          checkbox.indeterminate = true;
        },
      };

      syncMap[triState]();
    };

    handleUpdateCheckboxTriState(checkboxRef.current);
  }, [triState]);

  const titleClassNames = classnames(
    styles['checkbox__title'],
    isRequired && commonStyles['title_required'],
    titleClassName,
  );

  return (
    <div className={classnames(styles['checkbox__container'], containerClassName)}>
      <label htmlFor={checkboxId} className={classnames(styles['checkbox'], labelClassName)}>
        <input
          onClick={(event) => {
            if (readOnly) event.preventDefault();
            event.stopPropagation();
            onClick?.(event);
          }}
          type="checkbox"
          className={styles['checkbox__input']}
          checked={checked}
          disabled={disabled}
          readOnly={readOnly}
          {...props}
          ref={checkboxRef}
          id={checkboxId}
        />
        <div
          className={classnames(styles['checkbox__box'], !titlePosition && styles['checkbox__box--has-margin'])}
        ></div>
        {title && !titlePosition && <div className={titleClassNames}>{title}</div>}
      </label>
    </div>
  );
}

export function FormikCheckbox({ name, ...restProps }: TCheckboxProps & FieldHookConfig<boolean>) {
  const [field] = useField({ name, type: 'checkbox' });

  return <Checkbox {...field} {...restProps} />;
}
