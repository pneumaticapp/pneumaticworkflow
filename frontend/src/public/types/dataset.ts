export interface IDatasetItem {
  id?: number;
  value: string;
  order: number;
}

export interface IDataset {
  id: number;
  name: string;
  description: string;
  dateCreatedTsp: number;
  items: IDatasetItem[];
}

export interface IDatasetListItem {
  id: number;
  name: string;
  description: string;
  dateCreatedTsp: number;
  itemsCount: number;
}

export interface IGetDatasetsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: IDatasetListItem[];
}

export interface IGetDatasetsParams {
  ordering?: string;
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
}

export interface IGetDatasetParams {
  id: number;
  signal?: AbortSignal;
}

export interface ICreateDatasetParams {
  name: string;
  description?: string;
  items?: Omit<IDatasetItem, 'id'>[];
}

export interface IUpdateDatasetParams {
  id: number;
  name?: string;
  description?: string;
  items?: IDatasetItem[];
  signal?: AbortSignal;
}

export interface IDeleteDatasetParams {
  id: number;
}
export enum EDatasetsSorting {
  DateDesc = 'date-desc',
  DateAsc = 'date-asc',
  NameAsc = 'name-asc',
  NameDesc = 'name-desc',
}

export type TDatasetItemsSortOrder = 'asc' | 'desc';
