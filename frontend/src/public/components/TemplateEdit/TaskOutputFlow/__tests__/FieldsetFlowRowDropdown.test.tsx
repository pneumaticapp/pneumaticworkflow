// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Dropdown } from '../../../UI';
import { FieldsetFlowRowDropdown, IFieldsetFlowRowDropdownProps } from '../FieldsetFlowRowDropdown';

jest.mock('../../../UI', () => ({
  Dropdown: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  ArrowDownIcon: () => null,
  ArrowUpIcon: () => null,
  BurgerIcon: () => null,
  DropdownCrossIcon: () => null,
  TrashIcon: () => null,
}));

const formatMsg = (id: string) => intlMock.formatMessage({ id });

const getDropdownOptions = (): any[] => {
  const calls = (Dropdown as jest.Mock).mock.calls;
  return calls[calls.length - 1][0].options;
};

describe('FieldsetFlowRowDropdown', () => {
  const baseProps: IFieldsetFlowRowDropdownProps = {
    headerTitle: 'FS Title',
    isFirstItem: false,
    isLastItem: false,
    onMoveUp: jest.fn(),
    onMoveDown: jest.fn(),
    onRemove: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('isFirstItem=true → move-up option has isHidden: true', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isFirstItem: true }));

    const options = getDropdownOptions();
    const moveUp = options.find((o) => o.label === formatMsg('template.move-up'));
    expect(moveUp).toBeDefined();
    expect(moveUp.isHidden).toBe(true);
  });

  it('isFirstItem=false → move-up option has isHidden: false', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isFirstItem: false }));

    const options = getDropdownOptions();
    const moveUp = options.find((o) => o.label === formatMsg('template.move-up'));
    expect(moveUp).toBeDefined();
    expect(moveUp.isHidden).toBe(false);
  });

  it('isLastItem=true → move-down option has isHidden: true', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isLastItem: true }));

    const options = getDropdownOptions();
    const moveDown = options.find((o) => o.label === formatMsg('template.move-down'));
    expect(moveDown).toBeDefined();
    expect(moveDown.isHidden).toBe(true);
  });

  it('isLastItem=false → move-down option has isHidden: false', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isLastItem: false }));

    const options = getDropdownOptions();
    const moveDown = options.find((o) => o.label === formatMsg('template.move-down'));
    expect(moveDown).toBeDefined();
    expect(moveDown.isHidden).toBe(false);
  });

  it('onOpenDetail provided → options contain fieldset-flow-open-detail', () => {
    render(
      React.createElement(FieldsetFlowRowDropdown, {
        ...baseProps,
        onOpenDetail: jest.fn(),
      }),
    );

    const options = getDropdownOptions();
    const detailOption = options.find((o) => o.mapKey === 'fieldset-flow-open-detail');
    expect(detailOption).toBeDefined();
  });

  it('onOpenDetail not provided → options do not contain fieldset-flow-open-detail', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps }));

    const options = getDropdownOptions();
    const detailOption = options.find((o) => o.mapKey === 'fieldset-flow-open-detail');
    expect(detailOption).toBeUndefined();
  });
});
