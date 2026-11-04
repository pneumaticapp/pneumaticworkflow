import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { IAccountGenericTemplate } from '../types/genericTemplates';

export type TSaveAccountGenericTemplatesResponse = { genericTemplates: IAccountGenericTemplate[] };

export function saveAccountGenericTemplates(appIds: number[]) {
  return commonRequest<TSaveAccountGenericTemplatesResponse>('accountGenericTemplates', {
    method: 'POST',
    data: mapRequestBody({ appIds }),
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
