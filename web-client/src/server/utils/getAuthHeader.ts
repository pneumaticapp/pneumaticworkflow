import { EAppPart } from '../../public/utils/identifyAppPart/types';

export interface IAuthHeader {
  Authorization?: string;
  'User-Agent'?: string;
  'X-Guest-Authorization'?: string;
  'X-Public-Authorization'?: string;
}

interface IGetAuthHeaderParams {
  token?: string;
  appPart?: EAppPart;
  userAgent?: string;
}

const defaultParams = {
  token: '',
  appPart: EAppPart.MainApp,
};

export function getAuthHeader(params: IGetAuthHeaderParams = defaultParams) {
  const { token, appPart, userAgent } = { ...defaultParams, ...params };

  if (!token) {
    return {};
  }

  const authHeaderMap = {
    [EAppPart.MainApp]: { Authorization: `Bearer ${token}` },
    [EAppPart.PublicFormApp]: { 'X-Public-Authorization': `Token ${token}` },
    [EAppPart.GuestTaskApp]: { 'X-Guest-Authorization': token },
  };

  const userAgentHeader = userAgent && { 'User-Agent': userAgent };

  const headers: IAuthHeader = { ...authHeaderMap[appPart], ...userAgentHeader };

  return headers;
}
