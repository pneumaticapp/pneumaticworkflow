import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  cloneDatasetAction,
  deleteDatasetAction,
  updateDatasetAction,
  loadDataset,
} from '../../../redux/datasets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button, Placeholder } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { BoldPlusIcon } from '../../icons';
import { DatasetModal } from '../DatasetModal/DatasetModal';
import { EDatasetModalType } from '../DatasetModal/types';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';
import { DatasetRow } from '../DatasetRow/DatasetRow';

import { getCurrentDataset, isCurrentDatasetLoading } from '../../../redux/selectors/datasets';

import { TDatasetDetailsProps } from './types';
import styles from './DatasetDetails.css';

const DatasetDetails = ({ match: { params: { id: matchParamId } } }: TDatasetDetailsProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const dataset = useSelector(getCurrentDataset);
  const isLoading = useSelector(isCurrentDatasetLoading);
  const [isAddingRow, setIsAddingRow] = useState(false);

  useEffect(() => {
    dispatch(loadDataset({ id: Number(matchParamId) }));
  }, [matchParamId]);

  // TODO: replace with skeleton — render page layout with skeleton in header and list area
  if (isLoading || !dataset) {
    return null;
  }

  const handleAddRow = () => {
    setIsAddingRow(true);
  };

  const handleSaveNewRow = (value: string) => {
    const maxOrder = dataset.items.reduce((max, item) => Math.max(max, item.order), 0);

    // TODO: backend does not return the added row in the PATCH response
    dispatch(updateDatasetAction({
      id: dataset.id,
      items: [
        ...dataset.items,
        { value, order: maxOrder + 1 },
      ],
    }));

    setIsAddingRow(false);
  };

  const handleCancelNewRow = () => {
    setIsAddingRow(false);
  };

  const handleEditRow = (itemId: number, newValue: string) => {
    dispatch(updateDatasetAction({
      id: dataset.id,
      items: dataset.items.map((item) =>
        item.id === itemId ? { ...item, value: newValue } : item,
      ),
    }));
  };

  // TODO: backend does not return updated items in the PATCH response
  const handleDeleteRow = (itemId: number) => {
    dispatch(updateDatasetAction({
      id: dataset.id,
      items: dataset.items.filter((item) => item.id !== itemId),
    }));
  };

  const sortedItems = [...dataset.items].sort((a, b) => b.order - a.order);

  const renderItemList = () => {
    if (!dataset.items.length && !isAddingRow) {
      return (
        <Placeholder
          title={formatMessage({ id: 'datasets.empty-list.title' })}
          description={formatMessage({ id: 'datasets.empty-list.description' })}
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          containerClassName={styles['placeholder']}
        />
      );
    }

    return (
      <>
        {isAddingRow && (
          <DatasetRow
            isEditing
            onCancel={handleCancelNewRow}
            onSave={handleSaveNewRow}
            onDelete={handleCancelNewRow}
          />
        )}
        {sortedItems.map((item) => {
          return (
            <DatasetRow
              key={item.id}
              value={item.value}
              onSave={(newValue) => handleEditRow(item.id!, newValue)}
              onDelete={() => handleDeleteRow(item.id!)}
            />
          );
        })}
      </>
    );
  };

  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <h1 title={dataset.name}>{dataset.name}</h1>
        <div className={styles['header__config']}>
          <Button
            size="sm"
            icon={BoldPlusIcon}
            label={formatMessage({ id: 'datasets.add-row' })}
            buttonStyle="transparent-black"
            onClick={handleAddRow}
          />
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onClone={() => {
              dispatch(cloneDatasetAction({ id: dataset.id }));
              history.push(ERoutes.Datasets);
            }}
            onDelete={() => {
              dispatch(deleteDatasetAction({ id: dataset.id }));
              history.push(ERoutes.Datasets);
            }}
            editLabel={formatMessage({ id: 'datasets.edit' })}
            cloneLabel={formatMessage({ id: 'datasets.clone' })}
            deleteLabel={formatMessage({ id: 'datasets.delete' })}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>
      <div className={styles['list']}>
        {renderItemList()}
      </div>
      <DatasetModal type={EDatasetModalType.Edit} />
    </div>
  );
};

export default DatasetDetails;
