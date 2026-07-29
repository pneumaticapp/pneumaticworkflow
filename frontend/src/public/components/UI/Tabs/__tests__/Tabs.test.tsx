import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { Tabs, ITabsProps } from '../Tabs';

type TTabOption = { id: number; label: string };

const THREE_TABS: TTabOption[] = [
  { id: 1, label: 'First' },
  { id: 2, label: 'Second' },
  { id: 3, label: 'Third' },
];

const TWO_TABS: TTabOption[] = [
  { id: 1, label: 'Alpha' },
  { id: 2, label: 'Beta' },
];

const makeProps = (overrides: Partial<ITabsProps<TTabOption>> = {}): ITabsProps<TTabOption> => ({
  activeValueId: 1,
  values: THREE_TABS,
  onChange: jest.fn(),
  ...overrides,
});

const getTabButtons = () => screen.getAllByRole('button');

describe('Tabs — middle tab separator logic', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('middle tab gets separator-right when first tab is active', () => {
    render(React.createElement(Tabs, makeProps({ activeValueId: 1 })));

    const buttons = getTabButtons();
    expect(buttons[1].className).toContain('separator-right');
    expect(buttons[1].className).not.toContain('separator-left');
  });

  it('middle tab gets separator-left when third tab is active', () => {
    render(React.createElement(Tabs, makeProps({ activeValueId: 3 })));

    const buttons = getTabButtons();
    expect(buttons[1].className).toContain('separator-left');
    expect(buttons[1].className).not.toContain('separator-right');
  });

  it('middle tab gets no separator when it is active itself', () => {
    render(React.createElement(Tabs, makeProps({ activeValueId: 2 })));

    const buttons = getTabButtons();
    expect(buttons[1].className).not.toContain('separator-left');
    expect(buttons[1].className).not.toContain('separator-right');
  });

  it('no separator classes when there are only 2 tabs', () => {
    render(React.createElement(Tabs, makeProps({ values: TWO_TABS, activeValueId: 1 })));

    const buttons = getTabButtons();
    buttons.forEach((button) => {
      expect(button.className).not.toContain('separator');
    });
  });
});

describe('Tabs — active tab and click behavior', () => {
  beforeEach(() => { jest.clearAllMocks(); });

  it('applies tab_active class only to the active tab', () => {
    render(React.createElement(Tabs, makeProps({ activeValueId: 2 })));

    const buttons = getTabButtons();
    expect(buttons[0].className).not.toContain('tab_active');
    expect(buttons[1].className).toContain('tab_active');
    expect(buttons[2].className).not.toContain('tab_active');
  });

  it('calls onChange with the clicked tab id', () => {
    const onChange = jest.fn();
    render(React.createElement(Tabs, makeProps({ activeValueId: 1, onChange })));

    userEvent.click(screen.getByRole('button', { name: 'Third' }));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it('does not call onChange when clicking the already active tab', () => {
    const onChange = jest.fn();
    render(React.createElement(Tabs, makeProps({ activeValueId: 1, onChange })));

    userEvent.click(screen.getByRole('button', { name: 'First' }));

    expect(onChange).not.toHaveBeenCalled();
  });
});
