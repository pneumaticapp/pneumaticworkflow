import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { TemplateView } from '../Template';

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

describe('TemplateView — routing contract', () => {

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

  it('renders TemplateEdit (not FieldsetsView) for /templates/1/', () => {
    renderWithRoute('/templates/1/');

    expect(screen.getByTestId('template-edit')).toBeInTheDocument();
  });
});
