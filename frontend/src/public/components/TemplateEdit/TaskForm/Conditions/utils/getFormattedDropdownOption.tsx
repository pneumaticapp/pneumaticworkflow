import React, { ReactNode } from 'react';

import { DropdownOption } from '../../../../UI/DropdownList';

interface IGetFormattedDropdownOptionParams {
  label: string | ReactNode;
  isSelected?: boolean;
  isTooltip?: boolean;
}

export const getFormattedDropdownOption = ({ label, isSelected, isTooltip }: IGetFormattedDropdownOptionParams) => (
  <DropdownOption label={label} isSelected={isSelected} withTooltip={isTooltip} />
);
