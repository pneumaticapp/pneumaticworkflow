import React, { forwardRef } from 'react';

import { CustomInputProps } from './types';

export const CustomInput = forwardRef<HTMLInputElement, CustomInputProps>((props, ref) => {
  return <input {...props} ref={ref} readOnly />;
});
