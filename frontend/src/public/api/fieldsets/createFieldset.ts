import { commonRequest } from '../commonRequest';
import { IFieldsetTemplate, ICreateFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function createFieldset({ name, description, rules, fields }: ICreateFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IFieldsetTemplate>(
    urls.fieldsets,
    {
      method: 'POST',
      data: mapRequestBody({ name, description, rules, fields }),
    },
    {
      shouldThrow: true,
    },
  );
}
