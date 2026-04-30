import * as React from 'react';
import { useMemo } from 'react';
import { useSelector } from 'react-redux';

import { useTemplateEditFieldsetsCatalog } from '../../hooks/useTemplateEditFieldsetsCatalog';
import { IFieldsetData } from '../../types/template';
import { getTemplateData } from '../../redux/selectors/template';

export interface ITemplateEditFieldsetsContextValue {
  fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
  isLoading: boolean;
}

const defaultValue: ITemplateEditFieldsetsContextValue = {
  fieldsetsByApiName: new Map(),
  isLoading: false,
};

const TemplateEditFieldsetsContext = React.createContext<ITemplateEditFieldsetsContextValue>(defaultValue);

let fieldsetsByApiNameSnapshot: ReadonlyMap<string, IFieldsetData> = new Map();

export function getFieldsetsByApiNameSnapshot(): ReadonlyMap<string, IFieldsetData> {
  return fieldsetsByApiNameSnapshot;
}

export function useTemplateEditFieldsets(): ITemplateEditFieldsetsContextValue {
  return React.useContext(TemplateEditFieldsetsContext);
}

export function TemplateEditFieldsetsProvider({ children }: { children: React.ReactNode }) {
  const template = useSelector(getTemplateData);
  const { fieldsetsByApiName, isLoading } = useTemplateEditFieldsetsCatalog(template?.id);

  fieldsetsByApiNameSnapshot = fieldsetsByApiName;

  const value = useMemo(
    () => ({
      fieldsetsByApiName,
      isLoading,
    }),
    [fieldsetsByApiName, isLoading],
  );

  return (
    <TemplateEditFieldsetsContext.Provider value={value}>{children}</TemplateEditFieldsetsContext.Provider>
  );
}

