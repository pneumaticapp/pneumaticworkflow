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
  it('корректно рендерится', () => {
    const wrapper = shallow(<EditableField {...mockProps}/>);

    expect(wrapper).toMatchSnapshot();
  });
  it('рендерит ошибку, если значение не проходит валидацию', () => {
    const errorMsg = 'Length should be minimum five';
    const validate = (value: string) => value.length >= 5 ? '' : errorMsg;
    const wrapper = shallow(<EditableField {...mockProps} validate={validate} hiddenIcon />);
    wrapper.setState({touched: true});

    expect(wrapper.find(IntlMessages).prop('id')).toEqual(errorMsg);
  });
  it('если не рендерит иконку, то клик на элементе позволяет редактировать', () => {
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('click');

    expect(wrapper.state()).toEqual(expect.objectContaining({isEditable: true}));
  });
  it('при изменении вызывает changeValue из пропсов', () => {
    const textContent = 'edit result';
    const wrapper = shallow(<EditableField {...mockProps} hiddenIcon />);

    wrapper.find('span > span').simulate('input', {currentTarget: {textContent}});

    expect(mockProps.changeValue).toHaveBeenCalledWith(textContent);
  });
  it('при клике для редактирования устанавливает каретку в нужное место', () => {
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
  it('при клике для редактирования устанавливает каретку в нужное место', () => {
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
