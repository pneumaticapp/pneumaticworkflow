import { RouteComponentProps } from 'react-router-dom';

export interface IDatasetDetailsRouteParams {
  id: string;
}

export type TDatasetDetailsProps = RouteComponentProps<IDatasetDetailsRouteParams>;
