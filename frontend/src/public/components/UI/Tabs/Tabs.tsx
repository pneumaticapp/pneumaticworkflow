import * as React from 'react';
import { ReactNode } from 'react';
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

  const activeTabIndex = values.findIndex(checkIsActiveValue);

  return (
    <div className={classnames(styles['container'], containerClassName)}>
      {values.map((value, index) => {
        let middleTabBorderClass = '';
        if (values.length === 3 && activeTabIndex !== 1 && index === 1) {
          if (activeTabIndex === 0) middleTabBorderClass = styles['separator-right'];
          if (activeTabIndex === 2) middleTabBorderClass = styles['separator-left'];
        }

        return (
          <button
            key={value.id}
            type="button"
            onClick={handleClickItem(value)}
            className={classnames(
              styles['tab'],
              tabClassName,
              middleTabBorderClass,
              index === activeTabIndex && styles['tab_active'],
              index === activeTabIndex && activeTabClassName
            )}
          >
            {value.label}
          </button>
        );
      })}
    </div>
  );
}
