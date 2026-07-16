import React, { ReactElement } from 'react';
import { shallow } from 'enzyme';

import { Tooltip } from '../../UI';
import { SubMenuTooltip } from '../SubMenuItemTooltip';
import styles from '../SubMenuItemTooltip.css';

describe('SubMenuTooltip', () => {
  const renderTooltip = () =>
    shallow(
      <SubMenuTooltip containerClassName="menu-default" menuItems={[]}>
        <a href="/help">Help center</a>
      </SubMenuTooltip>,
    );

  it('uses the large arrow that matches the submenu caret dimensions', () => {
    expect(renderTooltip().find(Tooltip).prop('size')).toBe('lg');
  });

  it('uses a full-width element as the tooltip trigger', () => {
    const trigger = shallow(renderTooltip().find(Tooltip).prop('children') as ReactElement);

    expect(trigger.is('div')).toBe(true);
    expect(trigger.hasClass(styles['sub-menu__trigger'])).toBe(true);
  });
});
