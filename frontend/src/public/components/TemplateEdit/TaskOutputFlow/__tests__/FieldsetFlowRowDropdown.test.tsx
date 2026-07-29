import * as React from 'react';
import { render } from '@testing-library/react';

import { intlMock } from '../../../../__stubs__/intlMock';
import { Dropdown } from '../../../UI';
import { TDropdownOption } from '../../../UI/Dropdown/Dropdown';
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

const getDropdownOptions = (): TDropdownOption[] => {
  const calls = (Dropdown as jest.Mock).mock.calls;
  const options = calls[calls.length - 1][0].options;
  return Array.isArray(options) ? options : [];
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

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: formatMsg('template.move-up'),
          isHidden: true,
        }),
      ]),
    );
  });

  it('isFirstItem=false → move-up option has isHidden: false', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isFirstItem: false }));

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: formatMsg('template.move-up'),
          isHidden: false,
        }),
      ]),
    );
  });

  it('isLastItem=true → move-down option has isHidden: true', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isLastItem: true }));

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: formatMsg('template.move-down'),
          isHidden: true,
        }),
      ]),
    );
  });

  it('isLastItem=false → move-down option has isHidden: false', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps, isLastItem: false }));

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: formatMsg('template.move-down'),
          isHidden: false,
        }),
      ]),
    );
  });

  it('onOpenDetail provided → options contain fieldset-flow-open-detail', () => {
    render(
      React.createElement(FieldsetFlowRowDropdown, {
        ...baseProps,
        onOpenDetail: jest.fn(),
      }),
    );

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ mapKey: 'fieldset-flow-open-detail' }),
      ]),
    );
  });

  it('onOpenDetail not provided → options do not contain fieldset-flow-open-detail', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps }));

    expect(getDropdownOptions()).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ mapKey: 'fieldset-flow-open-detail' }),
      ]),
    );
  });

  it('every option calls closeDropdown strictly before the parent handler', () => {
    const onMoveUp = jest.fn();
    const onMoveDown = jest.fn();
    const onRemove = jest.fn();
    const onOpenDetail = jest.fn();
    render(
      React.createElement(FieldsetFlowRowDropdown, {
        ...baseProps,
        onMoveUp,
        onMoveDown,
        onRemove,
        onOpenDetail,
      }),
    );

    const options = getDropdownOptions();
    const findOption = (predicate: (o: TDropdownOption) => boolean): TDropdownOption => {
      const found = options.find(predicate);
      if (!found) throw new Error('Option not found by predicate');
      return found;
    };

    const cases: Array<{ option: TDropdownOption; handler: jest.Mock }> = [
      { option: findOption((o) => o.label === formatMsg('template.move-up')), handler: onMoveUp },
      { option: findOption((o) => o.label === formatMsg('template.move-down')), handler: onMoveDown },
      { option: findOption((o) => o.mapKey === 'fieldset-flow-open-detail'), handler: onOpenDetail },
      { option: findOption((o) => o.label === formatMsg('user.avatar.delete')), handler: onRemove },
    ];

    cases.forEach(({ option, handler }) => {
      const optionOnClick = option.onClick;
      if (!optionOnClick) {
        throw new Error(`Option "${String(option.label)}" has no onClick`);
      }
      const closeDropdown = jest.fn();
      optionOnClick(closeDropdown);

      expect(closeDropdown).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledTimes(1);
      expect(closeDropdown.mock.invocationCallOrder[0])
        .toBeLessThan(handler.mock.invocationCallOrder[0]);
    });
  });

  it('Delete option has withConfirmation, withUpperline and red color', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps }));

    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: formatMsg('user.avatar.delete'),
          withConfirmation: true,
          withUpperline: true,
          color: 'red',
        }),
      ]),
    );
  });

  it('Delete option is present regardless of onOpenDetail presence', () => {
    render(React.createElement(FieldsetFlowRowDropdown, { ...baseProps }));
    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: formatMsg('user.avatar.delete') }),
      ]),
    );

    (Dropdown as jest.Mock).mockClear();

    render(
      React.createElement(FieldsetFlowRowDropdown, {
        ...baseProps,
        onOpenDetail: jest.fn(),
      }),
    );
    expect(getDropdownOptions()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: formatMsg('user.avatar.delete') }),
      ]),
    );
  });
});
