import { commonRequest, TRequestType } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from '../utils/identifyAppPart/types';

const getRequestParams = (): [string, TRequestType] => {
  const { api: { urls }} = getBrowserConfigEnv();

  const appPart = identifyAppPartOnClient();

  const baseUrl = appPart !== EAppPart.PublicFormApp ? urls.attachment : urls.attachmentPublic;
  const type = appPart !== EAppPart.PublicFormApp ? 'local' : 'public';

  return [baseUrl, type];
};

export function deleteAttachment(id: number) {
  const [baseUrl, type] = getRequestParams();
  const url = baseUrl.replace(':id', String(id));

  return commonRequest(
    url,
    { method: 'DELETE' },
    { shouldThrow: true, responseType: 'empty', type },
  );
}
