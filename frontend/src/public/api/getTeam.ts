import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { EUserListSorting, EUserStatus, TUserListItem } from '../types/user';
import { isArrayWithItems } from '../utils/helpers';
import { identifyAppPartOnClient } from '../utils/identifyAppPart/identifyAppPartOnClient';
import { EAppPart } from  '../utils/identifyAppPart/types';

export interface IGetTeamResponse {
  count: number;
  next: string;
  previous: string;
  results: TUserListItem[];
}

export interface IGetTeamConfig {
  offset: number;
  limit: number;
  sorting: EUserListSorting;
  type?: TUserListItem['type'];
  status?: (EUserStatus.Active | EUserStatus.Inactive | EUserStatus.Invited)[];
}

const QS_BY_SORTING: {[key in EUserListSorting]: string} = {
  [EUserListSorting.NameAsc]: 'ordering=last_name',
  [EUserListSorting.NameDesc]: 'ordering=-last_name',
  [EUserListSorting.Status]: 'ordering=status',
};

export function getTeam({
  offset = 0,
  limit = 20,
  sorting = EUserListSorting.NameAsc,
  type,
  status,
}: Partial<IGetTeamConfig>) {
  return commonRequest<IGetTeamResponse>(
    `${getBaseUrl()}?${getTeamQueryString({limit, offset, sorting, type, status })}`,
    {}, {shouldThrow: true},
  );
}

const getBaseUrl = () => {
  const { api: { urls }} = getBrowserConfigEnv();

  const appPart = identifyAppPartOnClient();

  return appPart !== EAppPart.PublicFormApp ? urls.getUsers : urls.getUsersPublic;
};

export function getTeamQueryString({
  limit,
  offset,
  sorting,
  type,
  status,
}: IGetTeamConfig) {
  return [
    `limit=${limit}`,
    `offset=${offset}`,
    QS_BY_SORTING[sorting],
    type && `type=${type}`,
    isArrayWithItems(status) && `status=${status.join(',')}`,
  ].filter(Boolean).join('&');
}
