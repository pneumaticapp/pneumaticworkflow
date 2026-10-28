import * as React from 'react';
import { components } from 'react-select';

export function Option(props: any) {
  const { innerProps, data } = props;
  if (data.onClick) innerProps.onClick = data.onClick;

  return <components.Option {...props} />;
}
