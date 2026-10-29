import { getBrowserConfigEnv } from '../utils/getConfig';
import { buildQueryString } from '../utils/buildQueryString';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from '../utils/identifyAppPart/types';
import { commonRequest } from './commonRequest';
import type { IGetUsersConfig, TResponseUser } from './types';

const getUrl = () => {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const appPart = identifyAppPartOnClient();

  return appPart !== EAppPart.PublicFormApp ? urls.getUsers : urls.getUsersPublic;
};

export function getUsers(config?: IGetUsersConfig) {
  const url = getUrl() + getUsersQueryString(config);

  return commonRequest<TResponseUser[]>(url, {}, { shouldThrow: true });
}

export function getUsersQueryString(config?: IGetUsersConfig) {
  if (!config) {
    return '';
  }

  const { type, status, isAi } = config;

  return buildQueryString({ type, status, is_ai: isAi });
}
