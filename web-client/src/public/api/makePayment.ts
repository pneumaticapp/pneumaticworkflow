import { commonRequest } from './commonRequest';
import { mapRequestBody } from '../utils/mappers';
import { TPlanCode } from '../types/account';
import { getBrowserConfigEnv } from '../utils/getConfig';

interface IMakePaymentParams {
  successUrl: string;
  cancelUrl: string;
  code: TPlanCode;
  quantity: number;
}

export interface IMakePaymentResponse {
  paymentLink?: string;
}

export function makePayment({ successUrl, cancelUrl, code, quantity }: IMakePaymentParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IMakePaymentResponse>(
    urls.makePayment,
    {
      method: 'POST',
      body: mapRequestBody({
        successUrl,
        cancelUrl,
        products: [
          {
            code,
            quantity,
          },
        ],
      }),
    },
    {
      shouldThrow: true,
    },
  );
}
