import React, { type FocusEvent } from 'react';
import { FieldHookConfig, useField } from 'formik';

import { Select } from './Select';
import type { ISelectProps, TSelectOption } from './types';

export function FormikSelect(
  props: Omit<ISelectProps<TSelectOption>, 'options'> & {
    options: TSelectOption[];
  } & FieldHookConfig<string>,
) {
  const { name, onBlur: onBlurProp, options, type } = props;
  const [field, meta, { setTouched, setValue }] = useField(name);

  const handleChange = ({ value }: any) => setValue(value);

  const handleBlur = (event: FocusEvent<HTMLInputElement>) => {
    onBlurProp?.(event);
    // Let react-select finish an option click before validation rerenders it.
    window.setTimeout(() => setTouched(true), 0);
  };

  return (
    <Select
      {...props}
      onChange={handleChange}
      onBlur={handleBlur}
      // null, not undefined: with undefined react-select keeps displaying its previous internal selection.
      value={options.find((option) => option.value === field.value) ?? null}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}
