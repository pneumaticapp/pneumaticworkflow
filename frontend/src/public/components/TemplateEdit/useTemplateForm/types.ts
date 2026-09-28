import type { MutableRefObject, ReactNode } from 'react';
import { useFormik } from 'formik';

import { ITemplateClient } from '../../../types/template';

export type TSetFieldValue = (field: string, value: unknown, shouldValidate?: boolean) => void;
export type TSetValues = (
  values: ITemplateClient | ((currentValues: ITemplateClient) => ITemplateClient),
  shouldValidate?: boolean,
) => void;

export interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplateClient>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: MutableRefObject<boolean>;
  pendingUserEditsRef: MutableRefObject<Partial<ITemplateClient>>;
  persistBaselineSyncRef: MutableRefObject<((reduxTemplate: ITemplateClient) => void) | null>;
  children: ReactNode;
}

export interface ITemplateFormPersistProviderProps {
  dirtyRef: MutableRefObject<boolean>;
  pendingUserEditsRef: MutableRefObject<Partial<ITemplateClient>>;
  persistBaselineSyncRef: MutableRefObject<((reduxTemplate: ITemplateClient) => void) | null>;
  children: ReactNode;
}

export interface ITaskFormScopeProviderProps {
  taskUuid: string;
  children: ReactNode;
}

export interface ITemplateFieldContextValue {
  values: ITemplateClient;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
}

export interface ITemplatePersistContextValue {
  consumePendingChanges(explicitFields?: Partial<ITemplateClient>): Partial<ITemplateClient>;
  getRetryExplicitPatch(): Partial<ITemplateClient>;
  confirmConsumedChanges(): void;
  revertConsumedChanges(): void;
  abandonPendingChanges(): void;
}
