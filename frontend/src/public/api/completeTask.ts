import { getBrowserConfigEnv } from '../utils/getConfig';
import { IExtraField } from '../types/template';
import { mapRequestBody } from '../utils/mappers';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';

import { commonRequest } from './commonRequest';
import { ITaskAPI } from '../types/tasks';

export function completeTask(taskId: number, output: IExtraField[]) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.completeTask.replace(':id', String(taskId));

  const normalizedOutput = new ExtraFieldsHelper(output).normalizeFieldsValuesAsObject();

  return commonRequest<ITaskAPI>(
    url,
    {
      method: 'POST',
      data: mapRequestBody({ output: normalizedOutput }, 'default', {
        ignorePropertyMapToSnakeCase: ['output'],
      }),
    },
    {
      shouldThrow: true,
    },
  );
}
