import React from 'react';
import { FieldHookConfig, useField } from 'formik';

import { Select } from './Select';
import type { ISelectProps, TSelectOption } from './types';

export function FormikSelect(
  props: Omit<ISelectProps<TSelectOption>, 'options'> & {
    options: TSelectOption[];
  } & FieldHookConfig<string>,
) {
  const { name, options, type } = props;
  const [field, meta, { setValue }] = useField(name);

  const onChange = ({ value }: any) => setValue(value);

  return (
    <Select
      {...props}
      onChange={onChange}
      value={options.find((option) => option.value === field.value)}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}
