import { ITemplate } from '../../../types/template';

export type TSetFieldValue = (field: string, value: unknown, shouldValidate?: boolean) => void;
export type TSetValues = (values: ITemplate, shouldValidate?: boolean) => void;

export interface ITemplateFieldContextValue {
  values: ITemplate;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
}

export interface ITemplatePersistContextValue {
  consumePendingChanges(explicitFields?: Partial<ITemplate>): Partial<ITemplate>;
  /** Fields from a failed explicit submit (e.g. activation) to merge into the next retry. */
  getRetryExplicitPatch(): Partial<ITemplate>;
  /** Clears a revert snapshot after an explicit `patchTemplate` succeeds. */
  confirmConsumedChanges(): void;
  /** Restores the persist baseline and re-queues autosave when an explicit `patchTemplate` fails. */
  revertConsumedChanges(): void;
  /** Drops uncommitted edits without dispatching (e.g. after "Discard changes"). */
  abandonPendingChanges(): void;
}
