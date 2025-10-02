import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IPublicForm } from '../components/PublicFormsApp/common/types';

export type TPublicFormResponse = IPublicForm;

export function getPublicForm() {
  const { api: { urls } } = getBrowserConfigEnv();
  const url = urls.getPublicForm;

  return commonRequest<TPublicFormResponse>(
    url,
    {},
    { shouldThrow: true },
  );
}
