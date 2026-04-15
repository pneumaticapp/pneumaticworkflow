import * as React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { ArrowDownIcon, ArrowUpIcon, BurgerIcon, DropdownCrossIcon, TrashIcon } from '../../icons';
import { Dropdown, type TDropdownOption } from '../../UI';

import styles from '../KickoffRedux/KickoffRedux.css';

export interface IFieldsetFlowRowDropdownProps {
  headerTitle: string;
  isFirstItem: boolean;
  isLastItem: boolean;
  onMoveUp(): void;
  onMoveDown(): void;
  onRemove(): void;
  onOpenDetail?: () => void;
}

export const FieldsetFlowRowDropdown = ({
  headerTitle,
  isFirstItem,
  isLastItem,
  onMoveUp,
  onMoveDown,
  onRemove,
  onOpenDetail,
}: IFieldsetFlowRowDropdownProps) => {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const openDetailOption: TDropdownOption | null = onOpenDetail
    ? {
      mapKey: 'fieldset-flow-open-detail',
      label: formatMessage({ id: 'fieldsets.title' }),
      onClick: handleOptionClick(onOpenDetail),
    }
    : null;

  const menuOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'template.move-up' }),
      onClick: handleOptionClick(onMoveUp),
      Icon: ArrowUpIcon,
      isHidden: isFirstItem,
    },
    {
      label: formatMessage({ id: 'template.move-down' }),
      onClick: handleOptionClick(onMoveDown),
      Icon: ArrowDownIcon,
      isHidden: isLastItem,
    },
    ...(openDetailOption ? [openDetailOption] : []),
    {
      label: formatMessage({ id: 'user.avatar.delete' }),
      onClick: handleOptionClick(onRemove),
      Icon: TrashIcon,
      withConfirmation: true,
      withUpperline: true,
      color: 'red',
    },
  ];

  return (
    <Dropdown
      direction="right"
      className={styles['dropdown-wrapper']}
      renderToggle={(isOpen) => {
        const DropdownIcon = isOpen ? DropdownCrossIcon : BurgerIcon;

        return (
          <div className={classnames(styles['toggle'], isOpen && styles['toggle_active'])}>
            <DropdownIcon className={styles['toggle__icon']} />
          </div>
        );
      }}
      options={menuOptions}
      renderMenuContent={(renderedOptions) => (
        <>
          {headerTitle ? <div className={styles['dropdown-header']}>{headerTitle}</div> : null}
          <div className={styles['dropdown-items-wrapper']}>{renderedOptions}</div>
        </>
      )}
      menuClassName={styles['dropdown-menu']}
    />
  );
};
