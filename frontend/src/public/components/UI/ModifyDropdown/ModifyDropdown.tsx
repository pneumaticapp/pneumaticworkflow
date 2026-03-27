import React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import {
  TrashIcon,
  PencilIcon,
  UnionIcon,
  SettingsIcon,
} from '../../icons';

import { Dropdown , TDropdownOption } from '../Dropdown';
import { Button } from '../Buttons/Button';


import styles from './ModifyDropdown.css';

export interface IModifyDropdownProps {
  onEdit: () => void;
  onClone: () => void;
  onDelete: () => void;
  editLabel: string;
  cloneLabel: string;
  deleteLabel: string;
  className?: string;
}

export function ModifyDropdown({
  onEdit,
  onClone,
  onDelete,
  editLabel,
  cloneLabel,
  deleteLabel,
  className,
}: IModifyDropdownProps) {
  const { formatMessage } = useIntl();
  const options: TDropdownOption[] = [
    {
      label: editLabel,
      onClick: onEdit,
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: cloneLabel,
      onClick: onClone,
      Icon: UnionIcon,
      size: 'sm',
    },
    {
      label: deleteLabel,
      onClick: onDelete,
      Icon: TrashIcon,
      color: 'red',
      withUpperline: true,
      withConfirmation: true,
      size: 'sm',
    },
  ];

  return (
    <Dropdown
      renderToggle={() => (
        <Button
          size="sm"
          icon={SettingsIcon}
          label={formatMessage({ id: 'general.modify' })}
          buttonStyle="transparent-black"
          className={classNames(styles['toggle-btn'], className)}
        />
      )}
      options={options}
    />
  );
}
