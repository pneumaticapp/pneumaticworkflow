import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Dropdown } from '../../Dropdown';
import { Loader } from '../../Loader';
import { DropdownCloseIcon, EllipsisIcon } from '../../../icons';
import { IDropdownButtonProps } from './types';

import styles from './DropdownButton.css';

export function DropdownButton({ dropdownOptions, isLoading, isDisabled, className }: IDropdownButtonProps) {
  const { formatMessage } = useIntl();

  return (
    <div className={classnames(styles['dropdown-wrapper'], className)}>
      <Dropdown
        direction="right"
        isDisabled={isLoading || isDisabled}
        toggleProps={{ className: styles['btn-dropdown'] }}
        menuClassName={styles['dropdown-menu']}
        renderToggle={(isOpen) => {
          if (isLoading) return <Loader isLoading />;
          return isOpen ? <DropdownCloseIcon /> : <EllipsisIcon />;
        }}
      >
        {({ closeDropdown }) => dropdownOptions.map((item, index) => (
          <button
            type="button"
            className={styles['dropdown-item']}
            key={item.id || `${item.itemHeaderIntlId}-${item.itemDescriptionIntlId}-${index}`}
            onClick={() => {
              item.onClick();
              closeDropdown();
            }}
          >
            {item.itemHeaderIntlId && (
              <span className={styles['dropdown-item__header']}>
                {formatMessage({ id: item.itemHeaderIntlId })}
              </span>
            )}
            {item.itemDescriptionIntlId && (
              <span className={styles['dropdown-item__hint']}>
                {formatMessage({ id: item.itemDescriptionIntlId })}
              </span>
            )}
          </button>
        ))}
      </Dropdown>
    </div>
  );
}
