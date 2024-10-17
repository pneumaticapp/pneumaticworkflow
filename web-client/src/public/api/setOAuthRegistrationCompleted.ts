import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mergePaths } from '../utils/urls';
import { EOAuthType } from '../types/auth';

const { api: { urls }} = getBrowserConfigEnv();

export const OAUTH_URL_MAP: {[key in EOAuthType]: string} = {
  [EOAuthType.Microsoft]: urls.googleAuth,
  [EOAuthType.Google]: urls.googleAuth,
  [EOAuthType.SSO]: urls.googleAuth,
};

export function setOAuthRegistrationCompleted(id: string, type: EOAuthType) {
  return commonRequest<void>(
    ['/api/', OAUTH_URL_MAP[type], id, '/'].reduce(mergePaths),
    {
      method: 'PATCH',
      body: JSON.stringify({is_completed: true}),
      headers: {
        'Content-Type': 'application/json',
      },
    }, {
      type: 'local',
    });
}
