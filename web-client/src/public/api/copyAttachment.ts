import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

interface ICopyAttachmentResponse {
  id: number;
}

export function copyAttachment(id: number) {
  const { api: { urls }} = getBrowserConfigEnv();
  const url = urls.copyAttachment.replace(':id', String(id));

  return commonRequest<ICopyAttachmentResponse>(
    url,
    { method: 'POST' },
    { shouldThrow: true },
  );
}
