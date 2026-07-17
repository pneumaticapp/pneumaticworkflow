import { commonRequest } from '../commonRequest';
import { IFieldsetCatalogItem, IGetFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function getFieldset({ id, signal }: IGetFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.fieldset.replace(':id', String(id));

  return commonRequest<IFieldsetCatalogItem>(
    url,
    {
      method: 'GET',
      signal,
    },
    {
      shouldThrow: true,
    },
  );
}
