import { RouteComponentProps } from 'react-router-dom';

export interface IFieldsetDetailsRouteParams {
  templateId: string;
  id: string;
}

export type TFieldsetDetailsProps = RouteComponentProps<IFieldsetDetailsRouteParams>;
