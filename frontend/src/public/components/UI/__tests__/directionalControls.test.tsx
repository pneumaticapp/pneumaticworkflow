import React from 'react';
import { render, screen } from '@testing-library/react';
import { useIntl } from 'react-intl';
import { usePopper } from 'react-popper';

import { DropdownArea } from '../DropdownArea/DropdownArea';
import { DropdownList } from '../DropdownList/DropdownList';
import { Tooltip } from '../Tooltip/Tooltip';
import { CustomSlider } from '../../Slider/Slider';
import { InputField } from '../Fields/InputField/InputField';

jest.mock('react-intl', () => ({ ...jest.requireActual('react-intl'), useIntl: jest.fn() }));
jest.mock('react-popper', () => ({ usePopper: jest.fn() }));
jest.mock('react-select', () => ({
  __esModule: true,
  ...jest.requireActual('react-select'),
  default: ({ isRtl, placeholder }: { isRtl: boolean; placeholder: string }) => (
    <div data-testid="select" data-rtl={String(isRtl)}>
      {placeholder}
    </div>
  ),
}));
jest.mock('@tippyjs/react', () => ({
  __esModule: true,
  default: ({ placement, children }: { placement: string; children: React.ReactNode }) => (
    <div data-testid="tooltip" data-placement={placement}>
      {children}
    </div>
  ),
}));
jest.mock('rc-slider', () => ({
  __esModule: true,
  default: ({ reverse }: { reverse: boolean }) => <div data-testid="slider" data-reverse={String(reverse)} />,
  Handle: () => null,
}));

describe('shared controls use the active locale direction', () => {
  beforeEach(() => {
    (usePopper as jest.Mock).mockReturnValue({ styles: {}, attributes: {} });
  });

  it.each([
    ['en-US', false, 'bottom-start', 'right-start'],
    ['ru-RU', false, 'bottom-start', 'right-start'],
    ['ar-SY', true, 'bottom-end', 'left-start'],
  ])('adapts native library options and popup placement for %s', (locale, isRtl, popperPlacement, tooltipPlacement) => {
    (useIntl as jest.Mock).mockReturnValue({ locale, messages: {}, formatMessage: ({ id }: { id: string }) => id });

    render(
      <>
        <DropdownArea title="Menu">
          <span>Content</span>
        </DropdownArea>
        <DropdownList options={[]} />
        <Tooltip placement="right-start" content="Hint">
          <button>Target</button>
        </Tooltip>
        <CustomSlider />
      </>,
    );

    expect(usePopper).toHaveBeenLastCalledWith(expect.any(HTMLButtonElement), expect.any(HTMLDivElement), {
      placement: popperPlacement,
    });
    expect(screen.getByTestId('select')).toHaveAttribute('data-rtl', String(isRtl));
    expect(screen.getByTestId('select')).toHaveTextContent('ui.select-placeholder');
    expect(screen.getByTestId('tooltip')).toHaveAttribute('data-placement', tooltipPlacement);
    expect(screen.getByTestId('slider')).toHaveAttribute('data-reverse', String(isRtl));
  });

  it('preserves an explicit slider direction override', () => {
    (useIntl as jest.Mock).mockReturnValue({ locale: 'ar-SY' });
    render(<CustomSlider reverse={false} />);
    expect(screen.getByTestId('slider')).toHaveAttribute('data-reverse', 'false');
  });

  it('isolates a technical input without changing the surrounding document direction', () => {
    (useIntl as jest.Mock).mockReturnValue({
      locale: 'ar-SY',
      messages: {},
      formatMessage: ({ id }: { id: string }) => id,
    });
    document.documentElement.dir = 'rtl';
    const { unmount } = render(
      <InputField type="email" value="person@example.com" onChange={() => {}} onClear={() => {}} />,
    );

    expect(screen.getByTestId('input-field')).toHaveAttribute('dir', 'ltr');
    expect(screen.getByTestId('input-field')).toHaveClass('input-field_ltr');
    expect(document.documentElement).toHaveAttribute('dir', 'rtl');
    expect(screen.getByRole('button', { name: 'ui-input.clear' })).toBeVisible();

    unmount();
    document.documentElement.dir = 'ltr';
  });
});
