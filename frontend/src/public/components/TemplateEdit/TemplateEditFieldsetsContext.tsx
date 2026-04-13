import * as React from 'react';
import { useMemo } from 'react';

import { useTemplateEditFieldsetsCatalog } from '../../hooks/useTemplateEditFieldsetsCatalog';
import { IFieldsetData } from '../../types/template';

export interface ITemplateEditFieldsetsContextValue {
  fieldsetsById: ReadonlyMap<number, IFieldsetData>;
  isLoading: boolean;
}

const defaultValue: ITemplateEditFieldsetsContextValue = {
  fieldsetsById: new Map(),
  isLoading: false,
};

const TemplateEditFieldsetsContext = React.createContext<ITemplateEditFieldsetsContextValue>(defaultValue);

export function useTemplateEditFieldsets(): ITemplateEditFieldsetsContextValue {
  return React.useContext(TemplateEditFieldsetsContext);
}

export function TemplateEditFieldsetsProvider({ children }: { children: React.ReactNode }) {
  const { fieldsetsById, isLoading } = useTemplateEditFieldsetsCatalog();
  const value = useMemo(
    () => ({
      fieldsetsById,
      isLoading,
    }),
    [fieldsetsById, isLoading],
  );

  return (
    <TemplateEditFieldsetsContext.Provider value={value}>{children}</TemplateEditFieldsetsContext.Provider>
  );
}
