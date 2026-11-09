import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { Dropdown, DropdownToggle, DropdownMenu, DropdownItem } from 'reactstrap';
import { isRtlLocale } from '../../../../lang/direction';

import { Loader } from '../../Loader';
import { DropdownCloseIcon, EllipsisIcon } from '../../../icons';

import styles from './DropdownButton.css';

export interface IDropdownButtonOption {
  itemHeaderIntlId?: string;
  itemDescriptionIntlId?: string;
  onClick(): void;
}

export interface IDropdownButtonProps {
  dropdownOptions: IDropdownButtonOption[];
  isLoading?: boolean;
  isDisabled?: boolean;
  className?: string;
}

export function DropdownButton({ dropdownOptions, isLoading, isDisabled, className }: IDropdownButtonProps) {
  const { formatMessage, locale } = useIntl();

  const [isActive, setActiveState] = React.useState(false);

  const handleDropdownToggle = React.useCallback(() => {
    setActiveState(!isActive);
  }, [isActive]);

  const renderDropdownItem = (item: IDropdownButtonOption) => {
    const { itemHeaderIntlId, itemDescriptionIntlId, onClick } = item;

    return (
      <DropdownItem className={styles['dropdown-item']} onClick={onClick}>
        {itemHeaderIntlId && (
          <p className={styles['dropdown-item__header']}>{formatMessage({ id: itemHeaderIntlId })}</p>
        )}
        {itemDescriptionIntlId && (
          <p className={styles['dropdown-item__hint']}>{formatMessage({ id: itemDescriptionIntlId })}</p>
        )}
      </DropdownItem>
    );
  };

  const renderIcon = () => {
    if (isLoading) {
      return <Loader isLoading={isLoading} />;
    }

    return isActive ? <DropdownCloseIcon /> : <EllipsisIcon />;
  };

  return (
    <div className={classnames(styles['dropdown-wrapper'], className)}>
      <Dropdown isOpen={isActive} toggle={handleDropdownToggle}>
        <DropdownToggle
          tag="button"
          className={classnames(styles['btn-dropdown'], isActive && styles['btn-dropdown_active'])}
          disabled={isLoading || isDisabled}
        >
          {renderIcon()}
        </DropdownToggle>
        <DropdownMenu flip={false} className={styles['dropdown-menu']} right={!isRtlLocale(locale)}>
          {dropdownOptions.map(renderDropdownItem)}
        </DropdownMenu>
      </Dropdown>
    </div>
  );
}
