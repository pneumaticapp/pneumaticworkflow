import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { Dropdown, TDropdownOption } from '../../UI';
import { MoreIcon, PencilIcon, TrashIcon } from '../../icons';
import { WarningPopup } from '../../UI/WarningPopup';
import { openEditModal, deleteFieldsetAction, setCurrentFieldset } from '../../../redux/fieldsets/slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { sanitizeText } from '../../../utils/strings';
import { IFieldsetCardProps } from './types';

import styles from './FieldsetCard.css';

export function FieldsetCard({
  id,
  name,
  description,
  label_position,
  layout,
  order,
  rules,
  fields,
}: IFieldsetCardProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const handleOpenDeleteModal = () => setIsDeleteModalVisible(true);
  const handleCloseDeleteModal = () => setIsDeleteModalVisible(false);

  const handleConfirmDelete = () => {
    dispatch(deleteFieldsetAction({ id }));
    handleCloseDeleteModal();
  };

  const handleEditName = () => {
    dispatch(setCurrentFieldset({
      id,
      name,
      description,
      label_position,
      layout,
      order,
      rules,
      fields,
    }));
    dispatch(openEditModal());
  };

  const handleCardClick = () => {
    history.push(ERoutes.FieldsetDetail.replace(':id', id.toString()));
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'fieldsets.edit' }),
      onClick: handleEditName,
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'fieldsets.delete' }),
      onClick: handleOpenDeleteModal,
      Icon: TrashIcon,
      color: 'red',
      withUpperline: true,
      size: 'sm',
    },
  ];

  const hasContent = fields.length > 0 || rules.length > 0;

  return (
    <div className={styles['card']} key={id}>
      <WarningPopup
        acceptTitle={formatMessage({ id: 'fieldsets.delete' })}
        declineTitle={formatMessage({ id: 'fieldsets.modal-button-cancel' })}
        title={formatMessage({ id: 'fieldsets.delete.title' })}
        message={formatMessage({ id: 'fieldsets.delete.message' }, { name: <b>{name}</b> })}
        closeModal={handleCloseDeleteModal}
        isOpen={isDeleteModalVisible}
        onConfirm={handleConfirmDelete}
        onReject={handleCloseDeleteModal}
      />

      <div className={styles['card__content']}>
        <div className={styles['card__header']}>
          <div
            className={styles['card__title']}
            onClick={handleCardClick}
            onKeyDown={(e) => e.key === 'Enter' && handleCardClick()}
            role="link"
            tabIndex={0}
          >
            {sanitizeText(name)}
          </div>

          <Dropdown
            renderToggle={(isOpen: boolean) => (
              <MoreIcon className={classnames(styles['card__more'], isOpen && styles['is-active'])} />
            )}
            options={dropdownOptions}
          />
        </div>

        {hasContent && (
          <div className={styles['card__footer']}>
            {fields.length > 0 && (
              <div className={classnames(styles['card-stats'], styles['card-stats--items'])}>
                {formatMessage(
                  { id: 'fieldsets.stats.fields' },
                  { count: fields.length },
                )}
              </div>
            )}
            {rules.length > 0 && (
              <div className={classnames(styles['card-stats'], styles['card-stats--rules'])}>
                {formatMessage(
                  { id: 'fieldsets.stats.rules' },
                  { count: rules.length },
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
