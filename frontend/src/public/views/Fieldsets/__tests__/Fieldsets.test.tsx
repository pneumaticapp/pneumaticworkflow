import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { FieldsetsView } from '../Fieldsets';

jest.mock('@loadable/component', () => {
  const R = require('react');
  let callIndex = 0;
  const components = [
    () => R.createElement('div', { 'data-testid': 'fieldsets-list' }, 'FieldsetsList'),
    () => R.createElement('div', { 'data-testid': 'fieldset-details' }, 'FieldsetDetails'),
  ];
  return {
    __esModule: true,
    default: () => components[callIndex++] || (() => null),
  };
});

jest.mock('../../../components/UI', () => ({
  Loader: () => require('react').createElement('div', { 'data-testid': 'loader' }),
}));

describe('FieldsetsView — fieldsets routing contract', () => {

  const renderWithRoute = (url: string) => {
    return render(
      React.createElement(
        MemoryRouter,
        { initialEntries: [url] },
        React.createElement(FieldsetsView),
      ),
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders FieldsetDetails (not Fieldsets list) for /templates/1/fieldsets/2/', () => {
    renderWithRoute('/templates/1/fieldsets/2/');

    expect(screen.getByTestId('fieldset-details')).toBeInTheDocument();
    expect(screen.queryByTestId('fieldsets-list')).not.toBeInTheDocument();
  });

  it('renders Fieldsets list (not FieldsetDetails) for /templates/1/fieldsets/', () => {
    renderWithRoute('/templates/1/fieldsets/');

    expect(screen.getByTestId('fieldsets-list')).toBeInTheDocument();
    expect(screen.queryByTestId('fieldset-details')).not.toBeInTheDocument();
  });
});
