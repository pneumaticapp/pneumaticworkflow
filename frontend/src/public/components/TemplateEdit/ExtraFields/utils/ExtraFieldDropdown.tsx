import * as React from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';

import { IntlMessages } from '../../../IntlMessages';
import { ArrowDownIcon, ArrowRightIcon, ArrowUpIcon, BurgerIcon, DropdownCrossIcon, TrashIcon } from '../../../icons';
import { Dropdown, TDropdownOption } from '../../../UI';
import { IKickoffDropdownProps } from './types';

import styles from '../../KickoffRedux/KickoffRedux.css';

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
  showDatasetOption = false,
  datasetOptions,
  selectedDatasetId,
  onDatasetSelect,
}: IKickoffDropdownProps) {
  const { formatMessage } = useIntl();

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const getDatasetSubOptions = (): TDropdownOption[] | undefined => {
    if (!showDatasetOption || !datasetOptions?.length) {
      return undefined;
    }

    return datasetOptions.map((option) => {
      const isSelected = String(selectedDatasetId) === option.value;
      const isEmpty = option.itemsCount === 0;

      return {
        mapKey: `dataset-${option.value}`,
        label: option.label,
        disabled: isEmpty,
        className: classnames(styles['dataset-option'], isSelected && styles['dataset-option-selected']),
        onClick: (closeDropdown: () => void) => {
          onDatasetSelect?.(Number(option.value));
          closeDropdown();
        },
      };
    });
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
          label: formatMessage({ id: 'template.field-datasets-menu' }),
          isHidden: !showDatasetOption,
          Icon: ArrowRightIcon,
          className: classnames(styles['dataset-submenu'], !datasetOptions?.length && styles['dataset-disabled']),
          subOptions: getDatasetSubOptions(),
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
                aria-label={formatMessage({ id: 'template.kick-off-form-required' })}
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
                aria-label={formatMessage({ id: 'template.kick-off-form-hidden' })}
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
