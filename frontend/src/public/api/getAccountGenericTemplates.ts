import { commonRequest } from './commonRequest';
import type { IAccountGenericTemplate } from '../types/genericTemplates';

export type TGetAccountGenericTemplatesResponse = IAccountGenericTemplate[];

export function getAccountGenericTemplates() {
  return commonRequest<TGetAccountGenericTemplatesResponse>('accountGenericTemplates');
}
