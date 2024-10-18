import { IAPIMenuItemSub } from '../../../api/menu/getNavMenuItem';
import { IMenuItemSub } from '../../../types/menu';

export function mapArrayIAPIMenuSubToIMenuSub( arrMenuSub: IAPIMenuItemSub[] ): IMenuItemSub[] {
  return arrMenuSub.map(mapIAPIMenuSubToIMenuSub);
}

function mapIAPIMenuSubToIMenuSub({link, label, order, slug }: IAPIMenuItemSub): IMenuItemSub {
  return {
    id: slug,
    to: link,
    label,
    order,
  };
}
