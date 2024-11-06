import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { ITemplateResponse } from '../types/template';
import { mapRequestBody } from '../utils/mappers';
import { ETimeouts } from '../constants/defaultValues';

type TGeneratedTemplate = ITemplateResponse;

export function generateAITemplate(description: string, signal?: AbortSignal) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<TGeneratedTemplate>(
    urls.aiTemplate,
    {
      method: 'POST',
      body: mapRequestBody({ description }),
      signal,
    },
    {
      shouldThrow: true,
      timeOut: ETimeouts.Long,
    },
  );
}
