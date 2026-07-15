import React from 'react';

import { TemplatePersistContext } from './contexts';
import { ITemplateFormPersistProviderProps } from './types';
import {
  TEMPLATE_FORM_PERSIST_DEBOUNCE_MS,
  useTemplatePersistContextValue,
} from './useTemplatePersistContextValue';

export { TEMPLATE_FORM_PERSIST_DEBOUNCE_MS };

export function TemplateFormPersistProvider({
  dirtyRef,
  pendingUserEditsRef,
  persistBaselineSyncRef,
  children,
}: ITemplateFormPersistProviderProps) {
  const value = useTemplatePersistContextValue({
    dirtyRef,
    pendingUserEditsRef,
    persistBaselineSyncRef,
  });

  return (
    <TemplatePersistContext.Provider value={value}>
      {children}
    </TemplatePersistContext.Provider>
  );
}
