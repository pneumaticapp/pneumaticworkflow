import { commonRequest } from './commonRequest';

export interface IResendVerificationResponse {
  email: string;
}

export function resendVerification() {
  return commonRequest<IResendVerificationResponse>('resendVerification', {
    method: 'POST',
  }, {
    shouldThrow: true,
    type: 'local',
  });
}
