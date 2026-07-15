import type { MutableRefObject, ReactNode } from 'react';
import { useFormik } from 'formik';

import { ITemplate } from '../../../types/template';

export type TSetFieldValue = (field: string, value: unknown, shouldValidate?: boolean) => void;
export type TSetValues = (values: ITemplate, shouldValidate?: boolean) => void;

export interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: MutableRefObject<boolean>;
  pendingUserEditsRef: MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  children: ReactNode;
}

export interface ITemplateFormPersistProviderProps {
  dirtyRef: MutableRefObject<boolean>;
  pendingUserEditsRef: MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  children: ReactNode;
}

export interface ITaskFormScopeProviderProps {
  taskUuid: string;
  children: ReactNode;
}

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
