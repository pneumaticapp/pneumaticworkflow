import React from 'react';

import { ConditionDropdownOption } from '../ConditionDropdownOption';
import { IConditionDropdownOptionProps } from '../types';

type TGetFormattedDropdownOptionParams = Omit<IConditionDropdownOptionProps, 'withTooltip'> & {
  isTooltip?: boolean;
};

export const getFormattedDropdownOption = ({ label, isSelected, isTooltip }: TGetFormattedDropdownOptionParams) => (
  <ConditionDropdownOption label={label} isSelected={isSelected} withTooltip={isTooltip} />
);
