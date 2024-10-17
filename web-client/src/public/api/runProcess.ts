import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IStartWorkflowPayload } from '../redux/workflows/actions';

export type TRunProcessResponse = {
  name: string;
  currentTask: {
    performers: number[];
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
      body: mapRequestBody(data, 'default', {
        ignorePropertyMapToSnakeCase: ['kickoff'],
      }),
    },
    {
      shouldThrow: true,
    },
  );
}
