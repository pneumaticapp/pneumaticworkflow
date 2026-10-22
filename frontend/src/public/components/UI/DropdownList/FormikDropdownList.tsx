import * as React from 'react';
import type { FieldHookConfig } from 'formik';
import { useField } from 'formik';

import { DropdownList } from './DropdownList';
import type { IDropdownListProps, TDropdownOptionBase } from './types';

export function FormikDropdownList(props: IDropdownListProps<TDropdownOptionBase> & FieldHookConfig<string>) {
  const { name, onBlur: handleBlur, options, type } = props;
  const [field, meta, { setTouched, setValue }] = useField(name);

  const onChange = ({ value }: any) => setValue(value);
  const onBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    handleBlur?.(event);
    // Let react-select finish an option click before validation rerenders it.
    window.setTimeout(() => setTouched(true), 0);
  };

  return (
    <DropdownList
      {...props}
      onChange={onChange}
      onBlur={onBlur}
      // null, not undefined: with undefined react-select keeps displaying its previous internal selection.
      value={options.find((option) => option.value === field.value) ?? null}
      {...(meta.touched && meta.error && type !== 'hidden' && { errorMessage: meta.error })}
    />
  );
}
