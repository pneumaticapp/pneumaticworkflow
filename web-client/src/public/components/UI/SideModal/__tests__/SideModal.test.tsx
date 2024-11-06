/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { shallow } from 'enzyme';

import { SideModal } from '../SideModal';

const mockProps = {
  onClose: jest.fn(),
};

describe('SideModal', () => {
  it('rendered correctly', () => {
    const wrapper = shallow(<SideModal {...mockProps} />);

    expect(wrapper).toMatchSnapshot();
  });

  it('calls onClose when click close button', () => {
    const wrapper = shallow(<SideModal {...mockProps} />);
    const closeButton = wrapper.find('[data-test-id="close"]');
    closeButton.simulate('click');

    expect(mockProps.onClose).toHaveBeenCalled();
  });
});
