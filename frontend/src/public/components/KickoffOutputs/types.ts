import { IExtraField, IFieldsetData } from '../../types/template';

export type TOutputItem =
  | { kind: 'field'; order: number; data: IExtraField }
  | { kind: 'fieldset'; order: number; data: IFieldsetData };
