import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Dropdown, TDropdownOption } from '../../../UI';
import { EditIcon, MoreIcon, ReturnToIcon } from '../../../icons';

import styles from './KickoffMenu.css';

interface IKickoffMenuProps {
  isKickoffOpen: boolean;
  isClearDisabled: boolean;
  clearForm(): void;
  toggleKickoff(): void;
}

export function KickoffMenu({
  isKickoffOpen,
  isClearDisabled,
  toggleKickoff,
  clearForm,
}: IKickoffMenuProps) {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) =>  (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'kickoff.menu-edit' }),
      onClick: handleOptionClick(toggleKickoff),
      Icon: EditIcon,
      size: "sm",
      isHidden: isKickoffOpen,
    },
    {
      label: formatMessage({ id: 'kickoff.menu-close' }),
      onClick: handleOptionClick(toggleKickoff),
      size: "sm",
      isHidden: !isKickoffOpen,
    },
    {
      label: formatMessage({ id: 'kickoff.menu-clear' }),
      onClick: handleOptionClick(clearForm),
      Icon: ReturnToIcon,
      color: 'red',
      size: 'sm',
      withConfirmation: true,
      withUpperline: true,
      className: classnames(isClearDisabled && styles['disabled-option']),
    }
  ];

  return (
    <div className={styles['card-more-container']}>
      <Dropdown
        renderToggle={isOpen => (
          <MoreIcon
            className={classnames(styles['card-more'], isOpen && styles['card-more_active'])}
          />
        )}
        options={dropdownOptions}
      />
    </div>
  );
}
