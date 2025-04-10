import React, { forwardRef } from 'react';

import { CustomInputProps } from './types';



export const CustomInput = forwardRef<HTMLInputElement, CustomInputProps>(({ value, onClick, placeholder }, ref) => {
  return (
    <input ref={ref} value={value} onClick={onClick} placeholder={placeholder} readOnly />
  )
});
