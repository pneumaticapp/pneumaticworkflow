import { commonRequest } from './commonRequest';
import { EOAuthType } from '../types/auth';

export interface IGoogleRegisterInfoResponse {
  redirectUri: string;
}

const OAUTH_MAP_URL: { [key in EOAuthType]: string } = {
  [EOAuthType.Google]: 'oAuthGoogle',
  [EOAuthType.Microsoft]: 'oAuthMicrosoft',
  [EOAuthType.SSO]: 'oAuthSSO',
};

export function getOAuthUrl(type: EOAuthType) {
  return commonRequest<IGoogleRegisterInfoResponse>(OAUTH_MAP_URL[type], {}, { type: 'local' });
}
