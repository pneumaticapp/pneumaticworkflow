import { commonRequest, TRequestType } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { parseCookies } from '../utils/cookie';
import { mapRequestBody } from '../utils/mappers';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from  '../utils/identifyAppPart/types';

export interface IPublishAttachmentLinkResponse {
  url: string;
  thumbnailUrl?: string;
}

const getRequestParams = (): [string, TRequestType] => {
  const { api: { urls }} = getBrowserConfigEnv();

  const appPart = identifyAppPartOnClient();

  const baseUrl = appPart !== EAppPart.PublicFormApp ? urls.attachmentPublishLink : urls.attachmentPublishLinkPublic;
  const type = appPart !== EAppPart.PublicFormApp ? 'local' : 'public';

  return [baseUrl, type];
};

export function publishAttachmentLink(id: number) {
  const [baseUrl, type] = getRequestParams();
  const url = baseUrl.replace(':id', String(id));
  const { ajs_anonymous_id: anonymousId } = parseCookies(document.cookie);

  return commonRequest<IPublishAttachmentLinkResponse>(
    url,
    { method: 'POST', body: mapRequestBody({ anonymousId  }) },
    { shouldThrow: true, type },
  );
}
