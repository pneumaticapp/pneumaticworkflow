import { commonRequest } from '../commonRequest';
import { IFieldsetCatalogItem } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getAllFieldsetsCatalog(signal?: AbortSignal) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IFieldsetCatalogItem[]>(
    urls.fieldsets,
    {
      method: 'GET',
      signal,
    },
    {
      shouldThrow: true,
    },
  );
}
