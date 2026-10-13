import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IKickoff, ITemplateTask, TTemplateFieldFieldset } from '../types/template';

export type TGetTemplateFieldsResponse = {
  tasks: (Pick<ITemplateTask, 'id' | 'fields' | 'name' | 'apiName'> & {
    fieldsets: TTemplateFieldFieldset[];
  })[];
  kickoff: Pick<IKickoff, 'fields'> & {
    fieldsets: TTemplateFieldFieldset[];
  };
};

export function getTemplateFields(id: string, signal?: AbortSignal) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.templateFields.replace(':id', String(id));

  return commonRequest<TGetTemplateFieldsResponse>(url, { signal }, { shouldThrow: true });
}
