import * as React from 'react';
import { useState, useEffect, useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  cloneDatasetAction,
  deleteDatasetAction,
  updateDatasetAction,
  loadCurrentDataset,
  resetCurrentDataset,
} from '../../../redux/datasets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { BoldPlusIcon } from '../../icons';
import { DatasetModal } from '../DatasetModal/DatasetModal';
import { EDatasetModalType } from '../DatasetModal/types';
import { EDatasetsSorting } from '../../../types/dataset';
import { DatasetDetailsSkeleton } from './DatasetDetailsSkeleton';
import { DatasetItemsList } from './DatasetItemsList';

import { getSortedAndFilteredDatasetItems } from '../../../utils/dataset';

import { getCurrentDataset, isCurrentDatasetLoading } from '../../../redux/selectors/datasets';

import { TDatasetDetailsProps } from './types';
import styles from './DatasetDetails.css';

const DatasetDetails = ({ match: { params: { id: matchParamId } } }: TDatasetDetailsProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const dataset = useSelector(getCurrentDataset);
  const isLoading = useSelector(isCurrentDatasetLoading);
  const [isAddingRow, setIsAddingRow] = useState(false);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [searchText, setSearchText] = useState('');
  const [sorting, setSorting] = useState<EDatasetsSorting>(EDatasetsSorting.DateDesc);

  const sortedItems = useMemo(() => {
    return getSortedAndFilteredDatasetItems(dataset?.items || [], searchText, sorting);
  }, [dataset?.items, searchText, sorting]);

  const allItemValues = useMemo(
    () => dataset?.items.map((i) => i.value) || [],
    [dataset?.items],
  );

  useEffect(() => {
    const id = Number(matchParamId);
    if (Number.isNaN(id)) {
      history.push(ERoutes.Datasets);

      return;
    }
    if (dataset?.id === id) return;

    dispatch(loadCurrentDataset({ id }));
  }, [matchParamId]);

  useEffect(() => {
    return () => {
      dispatch(resetCurrentDataset());
    };
  }, []);

  if (isLoading || !dataset) {
    return <DatasetDetailsSkeleton />;
  }

  const handleAddRow = () => {
    setIsAddingRow(true);
    setEditingItemId(null);
    setSearchText('');
  };

  const handleSaveNewRow = (value: string) => {
    const maxOrder = dataset.items.reduce((max, item) => Math.max(max, item.order), 0);

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

  const handleStartEdit = (itemId: number) => {
    setEditingItemId(itemId);
    setIsAddingRow(false);
  };

  const handleCancelEdit = () => {
    setEditingItemId(null);
  };

  const handleEditRow = (itemId: number, newValue: string) => {
    dispatch(updateDatasetAction({
      id: dataset.id,
      items: dataset.items.map((item) =>
        item.id === itemId ? { ...item, value: newValue } : item,
      ),
    }));
    setEditingItemId(null);
  };

  const handleDeleteRow = (itemId: number) => {
    dispatch(updateDatasetAction({
      id: dataset.id,
      items: dataset.items.filter((item) => item.id !== itemId),
    }));
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
            className={styles['add-btn']}
            onClick={handleAddRow}
          />
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onClone={() => {
              dispatch(cloneDatasetAction({ id: dataset.id }));
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
      <DatasetItemsList
        sortedItems={sortedItems}
        allItemValues={allItemValues}
        isAddingRow={isAddingRow}
        editingItemId={editingItemId}
        searchText={searchText}
        sorting={sorting}
        onSearchChange={setSearchText}
        onSortingChange={setSorting}
        onSaveNewRow={handleSaveNewRow}
        onCancelNewRow={handleCancelNewRow}
        onStartEdit={handleStartEdit}
        onEditRow={handleEditRow}
        onCancelEdit={handleCancelEdit}
        onDeleteRow={handleDeleteRow}
      />
      <DatasetModal type={EDatasetModalType.Edit} />
    </div>
  );
};

export default DatasetDetails;
