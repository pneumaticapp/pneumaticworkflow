import { commonRequest } from '../commonRequest';
import { IFieldsetCatalogItem, ICreateFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function createFieldset(params: ICreateFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.fieldsets;

  return commonRequest<IFieldsetCatalogItem>(
    url,
    {
      method: 'POST',
      data: mapRequestBody(params),
    },
    {
      shouldThrow: true,
    },
  );
}
