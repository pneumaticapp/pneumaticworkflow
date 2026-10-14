import { EUserListSorting, EUserStatus } from '../../../types/user';
import { getUserNameForSorting } from '../../../utils/users';
import type { TTeamListItem } from './types';

const getItemName = (item: TTeamListItem): string =>
  item.kind === 'user' ? getUserNameForSorting(item.user) : item.agent.name.toLowerCase();

export const sortListItems = (items: TTeamListItem[], sorting: EUserListSorting): TTeamListItem[] => {
  const compareNames = (a: TTeamListItem, b: TTeamListItem) => {
    const [nameA, nameB] = [getItemName(a), getItemName(b)];

    return nameA > nameB ? 1 : nameA < nameB ? -1 : 0;
  };

  if (sorting === EUserListSorting.NameDesc) {
    return items.slice().sort((a, b) => compareNames(b, a));
  }

  if (sorting === EUserListSorting.Status) {
    const isInvitedUser = (item: TTeamListItem) => item.kind === 'user' && item.user.status === EUserStatus.Invited;

    return items
      .slice()
      .sort(compareNames)
      .sort((a, b) => {
        if (!isInvitedUser(a) && !isInvitedUser(b)) return 0;
        return isInvitedUser(a) ? 1 : -1;
      });
  }

  return items.slice().sort(compareNames);
};

export const matchesSearchQuery = (item: TTeamListItem, queryWords: string[]): boolean => {
  const fields = item.kind === 'user' ? [item.user.firstName, item.user.lastName, item.user.email] : [item.agent.name];
  const loweredFields = fields.map((str) => str.toLowerCase());

  return queryWords.every((queryWord) => loweredFields.some((field) => field.includes(queryWord)));
};
