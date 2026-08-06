import React from 'react';

import { DropdownOption } from '../../../UI/DropdownList';
import { IConditionDropdownOptionProps } from './types';

export function ConditionDropdownOption({
  label,
  isSelected,
  withTooltip,
}: IConditionDropdownOptionProps) {
  return (
    <DropdownOption
      label={label}
      isSelected={isSelected}
      withTooltip={withTooltip}
    />
  );
}
