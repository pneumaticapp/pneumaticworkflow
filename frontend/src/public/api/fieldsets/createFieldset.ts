import { commonRequest } from '../commonRequest';
import { IFieldsetTemplate, ICreateFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function createFieldset({ name, description, rules, fields }: ICreateFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.fieldsets;

  return commonRequest<IFieldsetTemplate>(
    url,
    {
      method: 'POST',
      data: mapRequestBody({ name, description, rules, fields }),
    },
    {
      shouldThrow: true,
    },
  );
}
