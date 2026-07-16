import { IExtraField } from '../../types/template';
import { IFieldsetRuntime } from '../../types/fieldset';

export type TOutputItem =
  | { kind: 'field'; order: number; data: IExtraField }
  | { kind: 'fieldset'; order: number; data: IFieldsetRuntime };