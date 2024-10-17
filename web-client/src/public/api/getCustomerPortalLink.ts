import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IGetCustomerPortalLinkResponse {
  link: string;
}

export function getCustomerPortalLink(cancelUrl: string) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.getCustomerPortalLink.replace(':cancel_url', cancelUrl);
  return commonRequest<IGetCustomerPortalLinkResponse>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}
