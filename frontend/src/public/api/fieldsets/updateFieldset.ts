import { commonRequest } from '../commonRequest';
import { IFieldsetCatalogItem, IUpdateFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function updateFieldset({ id, signal, ...data }: IUpdateFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.fieldset.replace(':id', String(id));

  return commonRequest<IFieldsetCatalogItem>(
    url,
    {
      method: 'PATCH',
      data: mapRequestBody(data),
      signal,
    },
    {
      shouldThrow: true,
    },
  );
}
