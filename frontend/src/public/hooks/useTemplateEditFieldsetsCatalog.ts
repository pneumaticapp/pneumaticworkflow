import { useEffect, useState } from 'react';

import { getFieldsets } from '../api/fieldsets/getFieldsets';
import { IFieldsetData } from '../types/template';
import { mapFieldsetTemplateToFieldsetData } from '../utils/mapFieldsetTemplateToFieldsetData';

export interface IUseTemplateEditFieldsetsCatalogResult {
  fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
  isLoading: boolean;
}

export function useTemplateEditFieldsetsCatalog(templateId: number | undefined): IUseTemplateEditFieldsetsCatalogResult {
  const [fieldsetsByApiName, setFieldsetsByApiName] = useState<ReadonlyMap<string, IFieldsetData>>(() => new Map());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!templateId) {
      setIsLoading(false);
      return undefined;
    }

    const abortController = new AbortController();

    setIsLoading(true);
    getFieldsets({ templateId, limit: 1000, signal: abortController.signal })
      .then((response) => {
        const nextMap = new Map<string, IFieldsetData>();
        response.results.forEach((item) => {
          const fieldsetData = mapFieldsetTemplateToFieldsetData(item);
          nextMap.set(fieldsetData.apiName, fieldsetData);
        });
        setFieldsetsByApiName(nextMap);
      })
      .catch(() => {
        // Aborted or network errors: keep previous map
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => abortController.abort();
  }, [templateId]);

  return { fieldsetsByApiName, isLoading };
}

