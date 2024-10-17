import { getNavMenuItem } from '../api/menu/getNavMenuItem';
import { getUserMenuItems, TMenuCounter } from '../constants/menu';
import { mapArrayIAPIMenuSubToIMenuSub } from '../redux/menu/utils/mapIAPIMenuToIMenu';
import { IMenuItem, TMenuCounterType } from '../types/menu';
import { IAuthUser } from '../types/redux';

// generate the menu items sequentially: first the top-level items, and then the sub-items
export function* generateMenuItems(user: IAuthUser, counters?: TMenuCounter[]): Generator<Promise<IMenuItem[]>> {
  const userMenuItems = getUserMenuItems(user, counters);

  yield Promise.resolve(userMenuItems);

  const itemsWithSubItems = Promise.all(userMenuItems.map(async item => {
    if (!item.subsSlug) {
      return item;
    }

    const subs = await getNavMenuItem(item.subsSlug);

    return {
      ...item,
      subs: subs?.items ? mapArrayIAPIMenuSubToIMenuSub(subs.items) : [],
    };
  }));

  yield itemsWithSubItems;
}

export const createMenuCounter = (id: IMenuItem['id'], value: number | null, type: TMenuCounterType = 'info'): TMenuCounter | null => {
  if (typeof value !== 'number') {
    return null;
  }

  return {
    id,
    value,
    type,
  }
}
