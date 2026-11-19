import type { IExtraField } from '../../types/template';
import type { IFieldsetRuntime } from '../../types/fieldset';

export type TOutputItem =
  { kind: 'field'; order: number; data: IExtraField } | { kind: 'fieldset'; order: number; data: IFieldsetRuntime };
