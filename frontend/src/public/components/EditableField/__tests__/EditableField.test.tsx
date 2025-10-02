import * as React from 'react';
import { shallow } from 'enzyme';

import { EditableField } from '../EditableField';
import { IntlMessages } from '../../IntlMessages';

const mockProps = {
  value: 'test',
  id: 'test-id',
  changeValue: jest.fn(),
};

describe('EditableField', () => {
  it('renders correctly', () => {
    const wrapper = shallow(<EditableField {...mockProps}/>);

    expect(wrapper).toMatchSnapshot();
  });
  it('renders an error if the value fails validation', () => {
    const errorMsg = 'Length should be minimum five';
    const validate = (value: string) => value.length >= 5 ? '' : errorMsg;
    const wrapper = shallow(<EditableField {...mockProps} validate={validate} hiddenIcon />);
    wrapper.setState({touched: true});

    expect(wrapper.find(IntlMessages).prop('id')).toEqual(errorMsg);
  });
  it('if it doesn’t render the icon, clicking on the element enables editing', () => {
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('click');

    expect(wrapper.state()).toEqual(expect.objectContaining({isEditable: true}));
  });
  it('on change, calls changeValue from props', () => {
    const textContent = 'edit result';
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('input', {currentTarget: {textContent}});

    expect(mockProps.changeValue).toHaveBeenCalledWith(textContent);
  });
  it('on click to edit, sets the caret in the desired position', () => {
    const focus = jest.fn();
    const current = {textContent: 'test', focus};
    jest.spyOn(React, 'createRef').mockReturnValueOnce({current});
    const range = {collapse: jest.fn(), selectNodeContents: jest.fn()};
    const selection = {addRange: jest.fn(), removeAllRanges: jest.fn()};
    window.getSelection = jest.fn().mockReturnValueOnce(selection as unknown as Selection);
    document.createRange = jest.fn().mockReturnValueOnce(range as unknown as Range);
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('click')

    expect(focus).toHaveBeenCalled();
    expect(range.selectNodeContents).toHaveBeenCalledWith(current);
    expect(range.collapse).toHaveBeenCalledWith(false);
    expect(selection.removeAllRanges).toHaveBeenCalled();
    expect(selection.addRange).toHaveBeenCalledWith(range);
  });
  it('on click to edit, places the caret in the correct position', () => {
    const focus = jest.fn();
    const current = {textContent: 'test', focus};
    jest.spyOn(React, 'createRef').mockReturnValueOnce({current});
    const range = {collapse: jest.fn(), selectNodeContents: jest.fn()};
    window.getSelection = jest.fn().mockReturnValueOnce(undefined as unknown as Selection);
    document.createRange = jest.fn().mockReturnValueOnce(range as unknown as Range);
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('click');

    expect(focus).toHaveBeenCalled();
    expect(range.selectNodeContents).toHaveBeenCalledWith(current);
    expect(range.collapse).toHaveBeenCalledWith(false);
  });
});
