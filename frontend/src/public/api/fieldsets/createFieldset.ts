import { commonRequest } from '../commonRequest';
import { IFieldsetTemplate, ICreateFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';
import { mapRequestBody } from '../../utils/mappers';

export function createFieldset({ templateId, name, description, rules, fields }: ICreateFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.templateFieldsets.replace(':id', String(templateId));

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
