import { commonRequest } from '../commonRequest';
import { IDeleteFieldsetParams } from '../../types/fieldset';
import { getBrowserConfigEnv } from '../../utils/getConfig';

export function deleteFieldset({ id }: IDeleteFieldsetParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.fieldset.replace(':id', String(id));

  return commonRequest<void>(
    url,
    {
      method: 'DELETE',
    },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}
