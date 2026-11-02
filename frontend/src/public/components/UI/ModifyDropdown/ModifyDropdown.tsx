import * as React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { TrashIcon, PencilIcon, UnionIcon, SettingsIcon, MoreIcon } from '../../icons';

import { DropdownMenu, TDropdownMenuOption } from '../DropdownMenu';

import { IModifyDropdownProps, EModifyDropdownToggle } from './types';

import buttonStyles from '../Buttons/Button/Button.css';
import styles from './ModifyDropdown.css';

export function ModifyDropdown({
  onEdit,
  onClone,
  onDelete,
  editLabel,
  cloneLabel,
  deleteLabel,
  isReadOnly,
  className,
  toggleType,
}: IModifyDropdownProps) {
  const { formatMessage } = useIntl();

  const options: TDropdownMenuOption[] = [
    {
      label: editLabel,
      onClick: onEdit,
      Icon: PencilIcon,
      size: 'sm',
      ...(isReadOnly && {
        isDisabled: true,
        disabledTooltip: formatMessage({ id: 'fieldsets.usage.disabled-tooltip' }),
      }),
    },
    ...(cloneLabel
      ? [
          {
            label: cloneLabel,
            onClick: onClone,
            Icon: UnionIcon,
            size: 'sm' as const,
          },
        ]
      : []),
    {
      label: deleteLabel,
      onClick: onDelete,
      Icon: TrashIcon,
      color: 'red' as const,
      withUpperline: true,
      withConfirmation: true,
      size: 'sm' as const,
      ...(isReadOnly && {
        isDisabled: true,
        disabledTooltip: formatMessage({ id: 'fieldsets.usage.disabled-tooltip' }),
      }),
    },
  ];

  const renderToggle = () => {
    if (toggleType === EModifyDropdownToggle.More) {
      return <MoreIcon className={className} />;
    }

    return (
      <span
        className={classNames(
          buttonStyles['button'],
          buttonStyles['button_sm'],
          buttonStyles['button_transparent-black'],
          buttonStyles['button_with-icon'],
          styles['toggle-btn'],
          className,
        )}
      >
        <SettingsIcon className={buttonStyles['icon']} />
        <span>{formatMessage({ id: 'general.modify' })}</span>
      </span>
    );
  };

  return <DropdownMenu renderToggle={renderToggle} options={options} />;
}
