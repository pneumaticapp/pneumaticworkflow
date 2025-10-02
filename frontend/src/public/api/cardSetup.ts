import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

interface ICardSetupParams {
  successUrl: string;
  cancelUrl: string;
}

export interface ICardSetupResponse {
  setupLink: string;
}

export function cardSetup({ successUrl, cancelUrl }: ICardSetupParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = `${urls.cardSetup}?success_url=${successUrl}&cancel_url=${cancelUrl}`;

  return commonRequest<ICardSetupResponse>(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}
