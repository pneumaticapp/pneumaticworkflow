/* eslint-disable jsx-a11y/label-has-associated-control */
import * as React from 'react';
import classnames from 'classnames';
import { FieldHookConfig, useField } from 'formik';

import styles from './Checkbox.css';
import commonStyles from '../common/styles.css';

export type TCheckboxTriState = 'checked' | 'empty' | 'indeterminate';

export interface ICheckboxProps {
  title?: string | React.ReactNode;
  isRequired?: boolean;
  containerClassName?: string;
  labelClassName?: string;
  titleClassName?: string;
  triState?: TCheckboxTriState;
}

type TCheckboxProps = ICheckboxProps &
  Pick<React.HTMLProps<HTMLInputElement>, 'checked' | 'disabled' | 'onChange' | 'id' | 'onClick'>;

// A checkbox can be controlled either with "checked" or "triState" prop.
// The difference is that the triState prop provides an indeterminate checkbox state.

export function Checkbox({
  title,
  isRequired,
  containerClassName,
  labelClassName,
  titleClassName,
  checked,
  disabled,
  triState,
  ...props
}: TCheckboxProps) {
  const checkboxRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => {
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
      <label className={classnames(styles['checkbox'], labelClassName)}>
        <input
          onClick={(e) => e.stopPropagation()}
          type="checkbox"
          className={styles['checkbox__input']}
          checked={checked}
          disabled={disabled}
          {...props}
          ref={checkboxRef}
        />
        <div className={styles['checkbox__box']}></div>
        {title && <p className={titleClassNames}>{title}</p>}
      </label>
    </div>
  );
}

export function FormikCheckbox({ name, ...restProps }: TCheckboxProps & FieldHookConfig<boolean>) {
  const [field] = useField({ name, type: 'checkbox' });

  return <Checkbox {...field} {...restProps} />;
}
