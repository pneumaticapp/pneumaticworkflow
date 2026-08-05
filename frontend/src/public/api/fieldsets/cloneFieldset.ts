import { commonRequest } from '../commonRequest';
import { IFieldsetCatalogItem } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function cloneFieldset(id: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.cloneFieldset.replace(':id', String(id));

  return commonRequest<IFieldsetCatalogItem>(
    url,
    {
      method: 'POST',
    },
    {
      shouldThrow: true,
    },
  );
}
