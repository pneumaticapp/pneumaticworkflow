import { commonRequest, TRequestType } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from  '../utils/identifyAppPart/types';

export interface IGetGoogleCloudSignedUrlRequest {
  accountId: number;
  filename: string;
  thumbnail: boolean;
  contentType: string;
  size: number;
}

export interface IAttachmentUploadUrlResponse {
  id: number;
  fileUploadUrl: string;
  thumbnailUploadUrl?: string;
}

const getRequestParams = (): [string, TRequestType] => {
  const { api: { urls }} = getBrowserConfigEnv();

  const appPart = identifyAppPartOnClient();

  const baseUrl = appPart !== EAppPart.PublicFormApp ? urls.attachmentUploadUrl : urls.attachmentUploadUrlPublic;
  const type = appPart !== EAppPart.PublicFormApp ? 'local' : 'public';

  return [baseUrl, type];
};

export function generateAttachmentUploadUrl(payload: IGetGoogleCloudSignedUrlRequest) {
  const [url, type] = getRequestParams();

  return commonRequest<IAttachmentUploadUrlResponse>(
    url,
    {
      method: 'POST',
      body: mapRequestBody(payload),
    },
    {
      shouldThrow: true,
      type,
    },
  );
}
