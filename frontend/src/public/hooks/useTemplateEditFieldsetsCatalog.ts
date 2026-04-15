import { useEffect, useState } from 'react';

import { getFieldsets } from '../api/fieldsets/getFieldsets';
import { IFieldsetData } from '../types/template';
import { mapFieldsetTemplateToFieldsetData } from '../utils/mapFieldsetTemplateToFieldsetData';

export interface IUseTemplateEditFieldsetsCatalogResult {
  fieldsetsById: ReadonlyMap<number, IFieldsetData>;
  isLoading: boolean;
}

export function useTemplateEditFieldsetsCatalog(templateId: number | undefined): IUseTemplateEditFieldsetsCatalogResult {
  const [fieldsetsById, setFieldsetsById] = useState<ReadonlyMap<number, IFieldsetData>>(() => new Map());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!templateId) {
      setIsLoading(false);
      return;
    }

    const abortController = new AbortController();

    setIsLoading(true);
    getFieldsets({ templateId, limit: 1000, signal: abortController.signal })
      .then((response) => {
        const nextMap = new Map<number, IFieldsetData>();
        response.results.forEach((item) => {
          nextMap.set(item.id, mapFieldsetTemplateToFieldsetData(item));
        });
        setFieldsetsById(nextMap);
      })
      .catch(() => {
        // Aborted or network errors: keep previous map
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => abortController.abort();
  }, [templateId]);

  return { fieldsetsById, isLoading };
}

