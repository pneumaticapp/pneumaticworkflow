import * as React from 'react';
import { useIntl } from 'react-intl';

import { Placeholder, SelectMenu, InputField } from '../../UI';
import { SearchMediumIcon } from '../../icons';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';
import { DatasetRow } from '../DatasetRow/DatasetRow';
import { EDatasetsSorting } from '../../../types/dataset';
import { datasetsSortingValues } from '../../../constants/sortings';
import { useCheckDevice } from '../../../hooks/useCheckDevice';

import { IDatasetItemsListProps } from './types';
import styles from './DatasetDetails.css';

export const DatasetItemsList = ({
  sortedItems,
  allItemValues,
  isAddingRow,
  editingItemId,
  searchText,
  sorting,
  onSearchChange,
  onSortingChange,
  onSaveNewRow,
  onCancelNewRow,
  onStartEdit,
  onEditRow,
  onCancelEdit,
  onDeleteRow,
}: IDatasetItemsListProps) => {
  const { formatMessage } = useIntl();
  const { isMobile } = useCheckDevice();

  const renderItems = () => {
    if (!sortedItems.length && !isAddingRow && !searchText) {
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
            existingItems={allItemValues}
            onCancel={onCancelNewRow}
            onSave={onSaveNewRow}
            onDelete={onCancelNewRow}
          />
        )}
        {sortedItems.map((item) => {
          const itemId = item.id;
          if (itemId === undefined) return null;

          return (
            <DatasetRow
              key={itemId}
              value={item.value}
              isEditing={editingItemId === itemId}
              existingItems={allItemValues}
              onEdit={() => onStartEdit(itemId)}
              onSave={(newValue) => onEditRow(itemId, newValue)}
              onCancel={onCancelEdit}
              onDelete={() => onDeleteRow(itemId)}
            />
          );
        })}
      </>
    );
  };

  return (
    <div className={styles['list']}>
      <div className={styles['toolbar']}>
        <div className={styles['search']}>
          <SearchMediumIcon className={styles['search__icon']} />
          <InputField
            value={searchText}
            onChange={(e) => onSearchChange(e.currentTarget.value)}
            className={styles['search-field__input']}
            placeholder={formatMessage({ id: 'datasets.search' })}
            onClear={() => onSearchChange('')}
          />
        </div>
        <SelectMenu
          activeValue={sorting}
          values={datasetsSortingValues}
          onChange={(val) => onSortingChange(val as EDatasetsSorting)}
          containerClassName={styles['dataset__sorting-container']}
          {...(isMobile && { activeValueLabelId: `datasets.sorting.${sorting}.mobile` })}
        />
      </div>
      {renderItems()}
    </div>
  );
};
