import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IStartWorkflowPayload } from '../redux/workflows/actions';
import { RawPerformer } from '../types/template';

export type TRunProcessResponse = {
  name: string;
  currentTask: {
    performers: RawPerformer[];
  };
};

export function runProcess(data: IStartWorkflowPayload) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.runTemplate.replace(':id', String(data.id));

  return commonRequest<TRunProcessResponse>(
    url,
    {
      method: 'POST',
      data: mapRequestBody(data, 'default', {
        ignorePropertyMapToSnakeCase: ['kickoff'],
      }),
    },
    {
      shouldThrow: true,
    },
  );
}
