import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import { IGroup } from '../../types/team';
import { EGroupsListSorting } from '../../types/user';

export interface IGetGroupsConfig {
  ordering: EGroupsListSorting;
}

export function getGroups(config: IGetGroupsConfig) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IGroup[]>(`${urls.groups}?${getGroupsQueryString(config)}`,
    {},
    { shouldThrow: true },);
}

export function getGroupsQueryString({ ordering }: IGetGroupsConfig) {
  const QS_BY_ORDERING: { [key in EGroupsListSorting]: string } = {
    [EGroupsListSorting.NameAsc]: 'ordering=name',
    [EGroupsListSorting.NameDesc]: 'ordering=-name',
  };

  return [QS_BY_ORDERING[ordering]].filter(Boolean).join('&');
}
