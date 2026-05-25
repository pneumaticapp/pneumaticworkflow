import React, { ReactNode } from 'react';
import classnames from 'classnames';

import styles from './Tabs.css';

type TOptionBase = {
  id: number | string;
  label: string | ReactNode;
};

export interface ITabsProps<TOption extends TOptionBase> {
  activeValueId: TOption['id'];
  values: TOption[];
  containerClassName?: string;
  tabClassName?: string;
  activeTabClassName?: string;
  onChange(value: TOption['id']): void;
}

export function Tabs<TOption extends TOptionBase>({
  activeValueId,
  values,
  containerClassName,
  tabClassName,
  activeTabClassName,
  onChange,
}: ITabsProps<TOption>) {
  const checkIsActiveValue = (value: TOption) => value.id === activeValueId;
  const handleClickItem = (value: TOption) => () => {
    if (!checkIsActiveValue(value)) {
      onChange(value.id);
    }
  };

  return (
    <div className={classnames(styles['container'], containerClassName)}>
      {values.map((value) => (
        <button
          key={value.id}
          type="button"
          onClick={handleClickItem(value)}
          className={classnames(
            styles['tab'],
            tabClassName,
            checkIsActiveValue(value) && styles['tab_active'],
            checkIsActiveValue(value) && activeTabClassName
          )}
        >
          {value.label}
        </button>
      ))}
    </div>
  );
}
