import { commonRequest } from './commonRequest';
import { getBrowserConfig } from '../utils/getConfig';

export enum EResetPasswordStatus {
  Valid = 0,
  Expired = 1,
  Invalid = 2,
}

export interface IConfirmResetPasswordResponse {
  status: EResetPasswordStatus;
}

export function confirmResetPassword(token: string) {
  const { config: { api: { urls }}} = getBrowserConfig();
  const url = `${urls.resetPassword}?token=${token}`;

  return commonRequest<IConfirmResetPasswordResponse>(url, {}, {
    type: 'local',
    shouldThrow: true,
  });
}
