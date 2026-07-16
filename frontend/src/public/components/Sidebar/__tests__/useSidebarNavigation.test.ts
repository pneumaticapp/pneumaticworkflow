import { IMenuItem } from '../../../types/menu';
import { getCurrentMenuItem } from '../useSidebarNavigation';

const menuItems: IMenuItem[] = [
  {
    id: 'dashboards',
    label: 'menu.dashboard',
    to: '/',
  },
  {
    id: 'help-center',
    label: 'menu.help-center',
    to: '/help',
    subs: [
      {
        id: 'templates',
        label: 'menu.help-center.templates',
        to: '/help/templates',
      },
    ],
  },
  {
    id: 'workflows',
    label: 'menu.workflows',
    to: '/workflows',
  },
];

describe('getCurrentMenuItem', () => {
  it('returns the parent item when a nested submenu route matches', () => {
    expect(getCurrentMenuItem(menuItems, '/help/templates/article')?.id).toBe('help-center');
  });

  it('prioritizes a submenu match over an earlier top-level prefix match', () => {
    expect(getCurrentMenuItem(menuItems, '/help/templates')?.id).toBe('help-center');
  });

  it('returns a directly matched top-level item', () => {
    expect(getCurrentMenuItem(menuItems, '/workflows/42')?.id).toBe('workflows');
  });
});
