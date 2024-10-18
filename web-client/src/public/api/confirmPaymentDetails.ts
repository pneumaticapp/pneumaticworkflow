import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

interface IConfirmPaymentDetailsParams {
  token: string;
}

export function confirmPaymentDetails({ token }: IConfirmPaymentDetailsParams) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.confirmPaymentDetails.replace(':token', token);

  return commonRequest(
    url,
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
      responseType: 'empty',
    },
  );
}
