import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { parseCookies } from '../utils/cookie';

type Fields = { [key: string]: string };

export type TRunPublicFornResponse = { redirectUrl: string | null };

export function runPublicForm(captcha: string, fields: Fields) {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.runPublicForm;

  const { ajs_anonymous_id: anonymousId } = parseCookies(document.cookie);

  return commonRequest<TRunPublicFornResponse>(
    url,
    {
      method: 'POST',
      body: mapRequestBody({ captcha, fields, anonymousId }, 'default', {ignorePropertyMapToSnakeCase: ['fields']}),
    },
    { shouldThrow: true, },
  );
}
