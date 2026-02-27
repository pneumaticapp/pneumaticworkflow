import * as React from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';

import { IntlMessages } from '../../../IntlMessages';
import { ArrowDownIcon, ArrowUpIcon, BurgerIcon, DropdownCrossIcon, TrashIcon } from '../../../icons';
import { IExtraField } from '../../../../types/template';
import { Dropdown } from '../../../UI';

import styles from '../../KickoffRedux/KickoffRedux.css';

interface IKickoffDropdownProps {
  apiName?: string;
  isRequired: boolean;
  isRequiredDisabled: boolean;
  isHidden?: boolean;
  isFirstItem?: boolean;
  isLastItem?: boolean;
  onEditField(changedProps: Partial<IExtraField>): void;
  onDeleteField(): void;
  onMoveFieldUp(): void;
  onMoveFieldDown(): void;
}

export function ExtraFieldDropdown({
  apiName,
  isRequired,
  isRequiredDisabled,
  isHidden = false,
  isFirstItem,
  isLastItem,
  onEditField,
  onDeleteField,
  onMoveFieldUp,
  onMoveFieldDown,
}: IKickoffDropdownProps) {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

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
      options={[
        {
          label: formatMessage({ id: 'template.move-up' }),
          onClick: handleOptionClick(onMoveFieldUp),
          Icon: ArrowUpIcon,
          isHidden: isFirstItem,
        },
        {
          label: formatMessage({ id: 'template.move-down' }),
          onClick: handleOptionClick(onMoveFieldDown),
          Icon: ArrowDownIcon,
          isHidden: isLastItem,
        },
        {
          mapKey: 'template.kick-off-form-required',
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
              <IntlMessages id="template.kick-off-form-required" />
              <Switch
                className={classnames(
                  'custom-switch custom-switch-primary custom-switch-small ml-auto',
                  styles['info-control_switch'],
                )}
                checked={isRequired}
                checkedChildren={null}
                unCheckedChildren={null}
                onChange={(isChecked) => onEditField({ isRequired: isChecked })}
                disabled={isRequiredDisabled || isHidden}
              />
            </div>
          ),
        },
        {
          mapKey: 'template.kick-off-form-hidden',
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
              <IntlMessages id="template.kick-off-form-hidden" />
              <Switch
                className={classnames(
                  'custom-switch custom-switch-primary custom-switch-small ml-auto',
                  styles['info-control_switch'],
                )}
                checked={isHidden}
                checkedChildren={null}
                unCheckedChildren={null}
                onChange={(isChecked) => onEditField({ isHidden: isChecked })}
                disabled={isRequired}
              />
            </div>
          ),
        },
        {
          label: formatMessage({ id: 'template.kick-off-form-delete-component' }),
          onClick: handleOptionClick(onDeleteField),
          Icon: TrashIcon,
          withConfirmation: true,
          withUpperline: true,
          color: 'red',
        },
      ]}
      renderMenuContent={(renderedOptions) => (
        <>
          {apiName && <div className={styles['dropdown-header']}>{apiName}</div>}
          <div className={styles['dropdown-items-wrapper']}>{renderedOptions}</div>
        </>
      )}
      menuClassName={styles['dropdown-menu']}
    />
  );
}
