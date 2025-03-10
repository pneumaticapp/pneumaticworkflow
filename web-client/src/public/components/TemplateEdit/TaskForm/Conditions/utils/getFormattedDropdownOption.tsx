import React, { ReactNode } from 'react';
import classnames from 'classnames';
import styles from '../Conditions.css';
import { Tooltip } from '../../../../UI';

interface IGetOptionState {
  label: string | ReactNode;
  isSelected?: boolean;
}

interface IGetFormattedDropdownOptionParams extends IGetOptionState {
  isTooltip?: boolean;
}

const STYLES = {
  selected: classnames(
    styles['condition__dropdown-option-is-selected'],
    styles['condition__value-field-select-option'],
  ),
  default: styles['condition__value-field-select-option'],
  tooltip: styles['condition__tooltop-box'],
};

const getOptionByState = ({ label, isSelected }: IGetOptionState) => {
  return isSelected ? <div className={STYLES.selected}>{label}</div> : <div className={STYLES.default}>{label}</div>;
};

export const getFormattedDropdownOption = ({ label, isSelected, isTooltip }: IGetFormattedDropdownOptionParams) => {
  if (isTooltip) {
    return (
      <Tooltip content={<div className={STYLES.tooltip}>{label}</div>} interactive={false}>
        {getOptionByState({ label, isSelected })}
      </Tooltip>
    );
  }

  return getOptionByState({ label, isSelected });
};
