import { commonRequest } from './commonRequest';
import { IAccountGenericTemplate } from '../types/genericTemplates';

export type TGetGenericTemplatesResponse = IAccountGenericTemplate[];

export function getGenericTemplates() {
  return commonRequest<TGetGenericTemplatesResponse>('getGenericTemplates');
}
