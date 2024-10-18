import { commonRequest } from './commonRequest';
import { IAccountGenericTemplate } from '../types/genericTemplates';

export type TGetAccountGenericTemplatesResponse = IAccountGenericTemplate[];

export function getAccountGenericTemplates() {
  return commonRequest<TGetAccountGenericTemplatesResponse>('accountGenericTemplates');
}
