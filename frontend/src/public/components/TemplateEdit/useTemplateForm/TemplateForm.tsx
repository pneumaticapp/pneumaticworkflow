import React, { useMemo } from 'react';
import { FormikProvider } from 'formik';

import { TemplateFieldContext } from './contexts';
import { TemplateFormPersistProvider } from './TemplateFormPersistProvider';
import { ITemplateFieldContextValue, ITemplateFormProps } from './types';

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
