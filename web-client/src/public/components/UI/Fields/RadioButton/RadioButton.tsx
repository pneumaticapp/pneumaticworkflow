/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { FieldHookConfig, useField } from 'formik';

import styles from './RadioButton.css';
import commonStyles from '../common/styles.css';

export interface IRadioButtonProps {
  title?: string | React.ReactNode;
  isRequired?: boolean;
  containerClassName?: string;
  labelClassName?: string;
  titleClassName?: string;
  id?: string;
}

type TRadioButtonProps = IRadioButtonProps & Pick<React.HTMLProps<HTMLInputElement>,
| 'checked'
| 'disabled'
| 'onChange'
>;

export function RadioButton({
  title,
  isRequired,
  containerClassName,
  labelClassName,
  titleClassName,
  checked,
  disabled,
  // tslint:disable-next-line: trailing-comma
  ...props
}: TRadioButtonProps) {

  const titleClassNames = classnames(
    styles['radio__title'],
    isRequired && commonStyles['title_required'],
    titleClassName,
  );

  return (
    <div className={containerClassName}>
      <label className={classnames(
        styles['radio'],
        labelClassName,
      )}>
        <input
          type="radio"
          className={styles['radio__input']}
          checked={checked}
          disabled={disabled}
          name={`${title}${props.id}`}
          {...props}
        />
        <span className={styles['radio__box']}></span>
        {title && (
          <span className={titleClassNames}>
            {title}
          </span>
        )}
      </label>
    </div>
  );
}

export function FormikRadioButton(props: TRadioButtonProps & FieldHookConfig<boolean>) {
  const [field] = useField({ name: props.name, type: 'radio' });

  return (
    <RadioButton
      {...props}
      {...field}
    />
  );
}
