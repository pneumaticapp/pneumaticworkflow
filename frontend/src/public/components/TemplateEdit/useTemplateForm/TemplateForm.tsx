import * as React from 'react';
import { useMemo } from 'react';
import { FormikProvider, useFormik } from 'formik';

import { ITemplate } from '../../../types/template';
import { TemplateFieldContext } from './contexts';
import { TemplateFormPersistProvider } from './TemplateFormPersistProvider';
import { TemplateValidationProvider, useTemplateValidation } from '../templateValidation';
import { ITemplateFieldContextValue, TSetFieldValue, TSetValues } from './types';

interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  openTask(taskUuid?: string): void;
  children: React.ReactNode;
}

/**
 * Bundles the Formik provider, the wrapped-setter context, and the single
 * persist provider so `TemplateEdit` only has to render `<TemplateForm .../>`.
 */
export function TemplateForm({
  formik,
  setFieldValue,
  setValues,
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
  openTask,
  children,
}: ITemplateFormProps) {
  return (
    <FormikProvider value={formik}>
      <TemplateValidationProvider openTask={openTask}>
        <TemplateFieldContextBridge
          formik={formik}
          setFieldValue={setFieldValue}
          setValues={setValues}
          dirtyRef={dirtyRef}
          pendingUserEditsRef={pendingUserEditsRef}
          persistBaselineSyncRef={persistBaselineSyncRef}
        >
          {children}
        </TemplateFieldContextBridge>
      </TemplateValidationProvider>
    </FormikProvider>
  );
}

interface ITemplateFieldContextBridgeProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
  children: React.ReactNode;
}

function TemplateFieldContextBridge({
  formik,
  setFieldValue,
  setValues,
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
  children,
}: ITemplateFieldContextBridgeProps) {
  const { values } = formik;
  const { clearValidation } = useTemplateValidation();

  const wrappedSetFieldValue = useMemo<TSetFieldValue>(
    () => (field, value, shouldValidate) => {
      clearValidation();
      setFieldValue(field, value, shouldValidate);
    },
    [clearValidation, setFieldValue],
  );

  const wrappedSetValues = useMemo<TSetValues>(
    () => (nextValues, shouldValidate) => {
      clearValidation();
      setValues(nextValues, shouldValidate);
    },
    [clearValidation, setValues],
  );

  const fieldContextValue = useMemo<ITemplateFieldContextValue>(
    () => ({ values, setFieldValue: wrappedSetFieldValue, setValues: wrappedSetValues }),
    [values, wrappedSetFieldValue, wrappedSetValues],
  );

  return (
    <TemplateFieldContext.Provider value={fieldContextValue}>
      <TemplateFormPersistProvider
        dirtyRef={dirtyRef}
        pendingUserEditsRef={pendingUserEditsRef}
        persistBaselineSyncRef={persistBaselineSyncRef}
      >
        {children}
      </TemplateFormPersistProvider>
    </TemplateFieldContext.Provider>
  );
}
