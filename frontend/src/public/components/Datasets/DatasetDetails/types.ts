import { RouteComponentProps } from 'react-router-dom';

import { EDatasetsSorting, IDatasetItem } from '../../../types/dataset';

export interface IDatasetDetailsRouteParams {
  id: string;
}

export type TDatasetDetailsProps = RouteComponentProps<IDatasetDetailsRouteParams>;

export interface IDatasetItemsListProps {
  sortedItems: IDatasetItem[];
  allItemValues: string[];
  isAddingRow: boolean;
  editingItemId: number | null;
  searchText: string;
  sorting: EDatasetsSorting;
  onSearchChange: (text: string) => void;
  onSortingChange: (sorting: EDatasetsSorting) => void;
  onSaveNewRow: (value: string) => void;
  onCancelNewRow: () => void;
  onStartEdit: (itemId: number) => void;
  onEditRow: (itemId: number, newValue: string) => void;
  onCancelEdit: () => void;
  onDeleteRow: (itemId: number) => void;
}
