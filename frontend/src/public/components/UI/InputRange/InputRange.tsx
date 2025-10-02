import * as React from 'react';

import styles from './InputRange.css';

export interface IInputRangeProps {
  min: number;
  max: number;
  value: number;
  onChange(value: number): void;
}

export function InputRange({min, max, value, onChange}: IInputRangeProps) {

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    onChange(+e.target.value);
  }

  const styleWidthIndicator = {
    width: `${((value - min) / (max - min)) * 100  }%`,
  };

  return (
    <div className={styles['cards-price-plan__range']}>
      <input
        data-testid="input-range"
        value={value}
        min={min}
        max={max}
        onChange={handleChange}
        type="range"/>
      <div className={styles['cards-price-plan__fullnes']}>
        <span style={styleWidthIndicator}></span>
      </div>
    </div>
  );
}
