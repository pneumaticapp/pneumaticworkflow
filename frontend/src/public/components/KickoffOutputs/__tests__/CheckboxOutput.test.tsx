// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { CheckboxOutput } from '../CheckboxOutput';
import { intlMock } from '../../../__stubs__/intlMock';

describe('CheckboxOutput', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const UNFILLED = formatMsg('template.kick-off-form-unfilled-value');

  const baseProps = {
    name: 'Colors',
    value: '',
    order: 0,
    type: 'checkbox' as any,
    apiName: 'colors',
    isRequired: false,
    userId: 1,
    groupId: 1,
  };

  it('displays string value as-is', () => {
    render(React.createElement(CheckboxOutput, { ...baseProps, value: 'opt1, opt2' }));

    expect(screen.getByText('opt1, opt2')).toBeInTheDocument();
  });

  it('displays array value joined with comma', () => {
    render(React.createElement(CheckboxOutput, { ...baseProps, value: ['opt1', 'opt2'] as any }));

    expect(screen.getByText('opt1, opt2')).toBeInTheDocument();
  });

  it('displays default unfilled text when value is empty', () => {
    render(React.createElement(CheckboxOutput, { ...baseProps, value: '' }));

    expect(screen.getByText(UNFILLED)).toBeInTheDocument();
  });
});
