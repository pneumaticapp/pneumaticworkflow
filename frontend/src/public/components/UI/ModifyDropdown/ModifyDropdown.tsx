import * as React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import {
  TrashIcon,
  PencilIcon,
  UnionIcon,
  SettingsIcon,
  MoreIcon,
} from '../../icons';

import { Dropdown , TDropdownOption } from '../Dropdown';

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
  className,
  toggleType,
}: IModifyDropdownProps) {
  const { formatMessage } = useIntl();
  const options: TDropdownOption[] = [
    {
      label: editLabel,
      onClick: onEdit,
      Icon: PencilIcon,
      size: 'sm',
    },
    ...(cloneLabel ? [{
      label: cloneLabel,
      onClick: onClone,
      Icon: UnionIcon,
      size: 'sm' as const,
    }] : []),
    {
      label: deleteLabel,
      onClick: onDelete,
      Icon: TrashIcon,
      color: 'red' as const,
      withUpperline: true,
      withConfirmation: true,
      size: 'sm' as const,
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

  return (
    <Dropdown
      renderToggle={renderToggle}
      options={options}
    />
  );
}
