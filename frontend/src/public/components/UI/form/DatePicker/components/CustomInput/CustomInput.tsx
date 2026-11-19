import React, { forwardRef } from 'react';

import type { CustomInputProps } from './types';

export const CustomInput = forwardRef<HTMLInputElement, CustomInputProps>((props, ref) => {
  return <input {...props} ref={ref} readOnly />;
});
