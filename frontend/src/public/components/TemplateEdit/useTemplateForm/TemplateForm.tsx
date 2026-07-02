import * as React from 'react';
import { useMemo } from 'react';
import { FormikProvider, useFormik } from 'formik';

import { ITemplate } from '../../../types/template';
import { TemplateFieldContext } from './contexts';
import { TemplateFormPersistProvider } from './TemplateFormPersistProvider';
import { ITemplateFieldContextValue, TSetFieldValue, TSetValues } from './types';

interface ITemplateFormProps {
  formik: ReturnType<typeof useFormik<ITemplate>>;
  setFieldValue: TSetFieldValue;
  setValues: TSetValues;
  dirtyRef: React.MutableRefObject<boolean>;
  pendingUserEditsRef: React.MutableRefObject<Partial<ITemplate>>;
  persistBaselineSyncRef: React.MutableRefObject<((reduxTemplate: ITemplate) => void) | null>;
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
  children,
}: ITemplateFormProps) {
  const { values } = formik;
  const fieldContextValue = useMemo<ITemplateFieldContextValue>(
    () => ({ values, setFieldValue, setValues }),
    [values, setFieldValue, setValues],
  );

  return (
    <FormikProvider value={formik}>
      <TemplateFieldContext.Provider value={fieldContextValue}>
        <TemplateFormPersistProvider
          dirtyRef={dirtyRef}
          pendingUserEditsRef={pendingUserEditsRef}
          persistBaselineSyncRef={persistBaselineSyncRef}
        >
          {children}
        </TemplateFormPersistProvider>
      </TemplateFieldContext.Provider>
    </FormikProvider>
  );
}
