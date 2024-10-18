import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';

export interface IGetCouponCodeResponse {
  name: string;
  couponCode: string;
  discountPercent: number;
}

export function getCouponCode(couponCode: string) {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<IGetCouponCodeResponse>(
    urls.getCouponCode.replace(':code', couponCode),
    {
      method: 'GET',
    },
    {
      shouldThrow: true,
    },
  );
}
