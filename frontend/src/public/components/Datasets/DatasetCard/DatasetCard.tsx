import * as React from 'react';
import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { Dropdown, TDropdownOption } from '../../UI';
import { MoreIcon, PencilIcon, TrashIcon, UnionIcon } from '../../icons';
import { WarningPopup } from '../../UI/WarningPopup';
import { openEditModal, deleteDatasetAction, setCurrentDataset, cloneDatasetAction } from '../../../redux/datasets/slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { sanitizeText } from '../../../utils/strings';
import { formatDateTimeAmPm } from '../../../utils/dateTime';
import { IDatasetCardProps } from './types';

import styles from './DatasetCard.css';

export function DatasetCard({
  id,
  name,
  description,
  dateCreatedTsp,
  itemsCount,
}: IDatasetCardProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const handleOpenDeleteModal = () => setIsDeleteModalVisible(true);
  const handleCloseDeleteModal = () => setIsDeleteModalVisible(false);

  const handleConfirmDelete = () => {
    dispatch(deleteDatasetAction({ id })); 
    handleCloseDeleteModal();
  };

  const handleEditName = () => {
    dispatch(setCurrentDataset({
      id,
      name,
      description,
      dateCreatedTsp,
      items: [],
    }));
    dispatch(openEditModal()); 
  };

  const handleCloneDataset = () => {
    dispatch(cloneDatasetAction({ id }));
  };

  const handleCardClick = () => {
    history.push(ERoutes.DatasetDetail.replace(':id', id.toString()));
  };
  
  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'datasets.edit' }),
      onClick: handleEditName,
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'datasets.clone' }),
      onClick: handleCloneDataset,
      Icon: UnionIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'datasets.delete' }),
      onClick: handleOpenDeleteModal,
      Icon: TrashIcon,
      color: 'red',
      withUpperline: true,
      size: 'sm',
    },
  ];

  const isFreshDataset = itemsCount === 0;

  return (
    <div className={styles['card']} key={id}>
      <WarningPopup
        acceptTitle={formatMessage({ id: 'datasets.delete' })}
        declineTitle={formatMessage({ id: 'datasets.modal-button-cancel' })}
        title={formatMessage({ id: 'datasets.delete.title' })}
        message={formatMessage({ id: 'datasets.delete.message' }, { name: <b>{name}</b> })}
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

        {!isFreshDataset && (
          <div className={styles['card__footer']}>
            <div className={classnames(styles['card-stats'], styles['card-stats--items'])}>
              {formatMessage(
                { id: 'datasets.stats.entries' },
                {
                  count: itemsCount,
                }
              )}
            </div>
            <div className={classnames(styles['card-stats'], styles['card-stats--date'])}>
              {formatMessage(
                { id: 'datasets.card.created' },
                {
                  date: formatDateTimeAmPm(dateCreatedTsp * 1000),
                }
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
