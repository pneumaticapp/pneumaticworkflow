import { getBrowserConfigEnv } from '../utils/getConfig';
import { IExtraField } from '../types/template';
import { mapRequestBody } from '../utils/mappers';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';

import { commonRequest } from './commonRequest';

export function completeTask(id: number, userId: number, taskId: number, output: IExtraField[]) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.completeTask.replace(':id', String(id));

  const normalizedOutput = new ExtraFieldsHelper(output).normalizeFieldsValuesAsObject();

  return commonRequest(url, {
    method: 'POST',
    body: mapRequestBody(
      { userId, taskId, output: normalizedOutput },
      'default',
      { ignorePropertyMapToSnakeCase: ['output'] }
    ),
  }, {
    responseType: 'empty',
    shouldThrow: true,
  });
}
