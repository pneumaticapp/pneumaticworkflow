import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EditIcon, MoreIcon } from '../../../icons';
import { DropdownMenu, TDropdownMenuOption } from '../../../UI';

import styles from './TemplateIntegrationsMenu.css';

interface ITemplateIntegrationsMenuProps {
  isOpen: boolean;
  toggle(): void;
}

export function TemplateIntegrationsMenu({ isOpen, toggle }: ITemplateIntegrationsMenuProps) {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const dropdownOptions: TDropdownMenuOption[] = [
    {
      label: formatMessage({ id: 'template.intergrations.menu-edit' }),
      onClick: handleOptionClick(toggle),
      Icon: EditIcon,
      size: 'sm',
      isHidden: isOpen,
    },
    {
      label: formatMessage({ id: 'template.intergrations.menu-close' }),
      onClick: handleOptionClick(toggle),
      size: 'sm',
      isHidden: !isOpen,
    },
  ];

  return (
    <div className={styles['card-more-container']}>
      <DropdownMenu
        renderToggle={(isDropdownOpen) => (
          <MoreIcon className={classnames(styles['card-more'], isDropdownOpen && styles['card-more_active'])} />
        )}
        options={dropdownOptions}
      />
    </div>
  );
}
