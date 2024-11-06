import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { IGenericTemplatesStore } from '../types/redux';

export type TSaveAccountGenericTemplatesResponse = Pick<IGenericTemplatesStore, 'genericTemplates'>;

export function saveAccountGenericTemplates(appIds: number[]) {
  return commonRequest<TSaveAccountGenericTemplatesResponse>('accountGenericTemplates', {
    method: 'POST',
    body: mapRequestBody({ appIds }),
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
