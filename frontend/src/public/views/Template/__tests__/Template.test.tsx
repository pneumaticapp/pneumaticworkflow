import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { TemplateView } from '../Template';

jest.mock('../../Fieldsets', () => ({
  FieldsetsView: () => React.createElement('div', { 'data-testid': 'fieldsets-view' }, 'FieldsetsView'),
}));

jest.mock('@loadable/component', () => ({
  __esModule: true,
  default: () => {
    const Lazy = () => React.createElement('div', { 'data-testid': 'template-edit' }, 'TemplateEdit');

    return Lazy;
  },
}));

jest.mock('../../../layout', () => ({
  TemplateLayout: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'template-layout' }, children),
}));

jest.mock('../../../components/UI', () => ({
  Loader: () => React.createElement('div', { 'data-testid': 'loader' }),
}));

describe('TemplateView — fieldsets routing contract', () => {

  const renderWithRoute = (url: string) => {
    return render(
      React.createElement(
        MemoryRouter,
        { initialEntries: [url] },
        React.createElement(TemplateView),
      ),
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders FieldsetsView (not TemplateEdit) for /templates/1/fieldsets/', () => {
    renderWithRoute('/templates/1/fieldsets/');

    expect(screen.getByTestId('fieldsets-view')).toBeInTheDocument();
    expect(screen.queryByTestId('template-edit')).not.toBeInTheDocument();
  });

  it('renders FieldsetsView for nested /templates/1/fieldsets/2/', () => {
    renderWithRoute('/templates/1/fieldsets/2/');

    expect(screen.getByTestId('fieldsets-view')).toBeInTheDocument();
    expect(screen.queryByTestId('template-edit')).not.toBeInTheDocument();
  });

  it('renders TemplateEdit (not FieldsetsView) for /templates/1/', () => {
    renderWithRoute('/templates/1/');

    expect(screen.getByTestId('template-edit')).toBeInTheDocument();
    expect(screen.queryByTestId('fieldsets-view')).not.toBeInTheDocument();
  });
});
