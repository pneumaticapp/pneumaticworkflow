// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { RadioOutput } from '../RadioOutput';
import { intlMock } from '../../../__stubs__/intlMock';

describe('RadioOutput', () => {
  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const UNFILLED = formatMsg('template.kick-off-form-unfilled-value');

  const baseProps = {
    name: 'Color',
    value: '',
    order: 0,
    type: 'radio' as any,
    apiName: 'color',
    isRequired: false,
    userId: 1,
    groupId: 1,
  };

  it('displays value when provided', () => {
    render(React.createElement(RadioOutput, { ...baseProps, value: 'option1' }));

    expect(screen.getByText('option1')).toBeInTheDocument();
  });

  it('displays default unfilled text when value is empty', () => {
    render(React.createElement(RadioOutput, { ...baseProps, value: '' }));

    expect(screen.getByText(UNFILLED)).toBeInTheDocument();
  });
});
