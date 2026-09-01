import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DeletableDropdownOption } from '../DeletableDropdownOption';

jest.mock('../../../../icons', () => ({
  TrashIcon: (props: React.SVGAttributes<SVGSVGElement>) =>
    React.createElement('svg', { ...props, 'data-testid': 'trash-icon' }),
}));

jest.mock('../DeletableDropdownOption.css', () => new Proxy({}, { get: (_t, k) => String(k) }));
jest.mock('../../../../UI/Dropdown/Dropdown.css', () => new Proxy({}, { get: (_t, k) => String(k) }));

const intlMock = require('react-intl').useIntl();
const formatMsg = (id: string) => intlMock.formatMessage({ id });

const SURE_LABEL = formatMsg('dropdown.are-you-sure');
const YES_LABEL = formatMsg('dropdown.yes');
const NO_LABEL = formatMsg('dropdown.no');

describe('DeletableDropdownOption', () => {
  const defaultProps = {
    label: 'Rule 1',
    onDelete: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders label and delete icon in normal mode', () => {
    render(<DeletableDropdownOption {...defaultProps} />);

    expect(screen.getByText('Rule 1')).toBeInTheDocument();
    expect(screen.getByTestId('trash-icon')).toBeInTheDocument();
  });

  it('switches to confirmation mode when delete icon is clicked', () => {
    render(<DeletableDropdownOption {...defaultProps} />);

    userEvent.click(screen.getByTestId('trash-icon'));

    expect(screen.getByText(SURE_LABEL)).toBeInTheDocument();
    expect(screen.getByText(YES_LABEL)).toBeInTheDocument();
    expect(screen.getByText(NO_LABEL)).toBeInTheDocument();
    expect(screen.queryByText('Rule 1')).not.toBeInTheDocument();
  });

  it('calls onDelete when Yes is clicked', () => {
    render(<DeletableDropdownOption {...defaultProps} />);

    userEvent.click(screen.getByTestId('trash-icon'));
    userEvent.click(screen.getByText(YES_LABEL));

    expect(defaultProps.onDelete).toHaveBeenCalledTimes(1);
  });

  it('returns to normal mode when No is clicked', () => {
    render(<DeletableDropdownOption {...defaultProps} />);

    userEvent.click(screen.getByTestId('trash-icon'));
    userEvent.click(screen.getByText(NO_LABEL));

    expect(screen.getByText('Rule 1')).toBeInTheDocument();
    expect(screen.getByTestId('trash-icon')).toBeInTheDocument();
    expect(screen.queryByText(SURE_LABEL)).not.toBeInTheDocument();
  });

  it('switches to confirmation mode when Enter is pressed on delete icon', () => {
    render(<DeletableDropdownOption {...defaultProps} />);

    const trashIcon = screen.getByTestId('trash-icon');
    userEvent.type(trashIcon, '{enter}');

    expect(screen.getByText(SURE_LABEL)).toBeInTheDocument();
  });

  it('calls onClick when label is clicked', () => {
    const onClick = jest.fn();
    render(<DeletableDropdownOption {...defaultProps} onClick={onClick} />);

    userEvent.click(screen.getByText('Rule 1'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not trigger onClick when trash icon is clicked', () => {
    const onClick = jest.fn();
    render(<DeletableDropdownOption {...defaultProps} onClick={onClick} />);

    userEvent.click(screen.getByTestId('trash-icon'));

    expect(onClick).not.toHaveBeenCalled();
  });
});
