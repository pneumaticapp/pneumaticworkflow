import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { IPublicFormResponse } from '../types/publicForms';

export type TPublicFormResponse = IPublicFormResponse;

export function getPublicForm() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.getPublicForm;

  return commonRequest<TPublicFormResponse>(url, {}, { shouldThrow: true });
}
