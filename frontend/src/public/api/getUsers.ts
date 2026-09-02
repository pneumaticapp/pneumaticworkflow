import { EUserStatus, TUserListItem } from '../types/user';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { isArrayWithItems } from '../utils/helpers';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from  '../utils/identifyAppPart/types';
import { commonRequest } from './commonRequest';

export type TResponseUser = TUserListItem[];

export interface IGetUsersConfig {
  type?: TUserListItem['type'];
  status?: (EUserStatus.Active | EUserStatus.Inactive | EUserStatus.Invited)[];
  /** Pass false to keep AI agents out of the list; omit to leave them in. */
  isAi?: boolean;
}

const getUrl = () => {
  const { api: { urls }} = getBrowserConfigEnv();

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

  const queryString = [
    type && `type=${type}`,
    isArrayWithItems(status) && `status=${status.join(',')}`,
    // Compared against undefined: false is a meaningful value here and must still be sent.
    isAi !== undefined && `is_ai=${isAi}`,
  ].filter(Boolean).join('&');

  return queryString ? `?${queryString}` : '';
}
