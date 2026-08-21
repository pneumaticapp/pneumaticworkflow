import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';
import { IntlProvider } from 'react-intl';

import { TemplateLayout } from '../TemplateLayout';
import { EGraphViewMode } from '../../../components/TemplateEdit/TemplateGraphEditor/types';
import { ERoutes } from '../../../constants/routes';
import { setViewMode } from '../../../redux/templateGraphView/slice';
import { enMessages } from '../../../lang/locales/en_US';

jest.mock('../../../components/TopNav', () => ({
  TopNavContainer: ({ leftContent }: { leftContent: React.ReactNode }) => (
    <div>{leftContent}</div>
  ),
}));

jest.mock('../../../components/UI', () => ({
  Tabs: ({
    values,
    onChange,
    activeValueId,
  }: {
    values: { id: string; label: React.ReactNode }[];
    onChange: (id: string) => void;
    activeValueId: string;
  }) => (
    <div>
      {values.map((value) => (
        <button
          key={String(value.id)}
          type="button"
          onClick={() => {
            if (value.id !== activeValueId) {
              onChange(value.id);
            }
          }}
        >
          {value.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock('../../../utils/history', () => ({
  history: {
    push: jest.fn(),
    location: { pathname: '/templates/edit/1/' },
    listen: jest.fn(),
  },
}));

const mockDispatch = jest.fn();

const renderLayout = (
  viewMode: EGraphViewMode = EGraphViewMode.List,
  selectedTaskApiName: string | null = null,
) => {
  (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  (useSelector as jest.Mock).mockImplementation((selector: (state: unknown) => unknown) =>
    selector({
      templateGraphView: {
        viewMode,
        selectedTaskApiName,
      },
    }),
  );

  return render(
    <IntlProvider locale="en" messages={enMessages}>
      <MemoryRouter>
        <TemplateLayout>
          <div>editor-content</div>
        </TemplateLayout>
      </MemoryRouter>
    </IntlProvider>,
  );
};

describe('TemplateLayout', () => {
  beforeEach(() => {
    mockDispatch.mockClear();
    document.body.classList.remove('template-graph-lock');
  });

  afterEach(() => {
    document.body.classList.remove('template-graph-lock');
    document.getElementById('app-container')?.classList.remove('template-graph-lock');
  });

  it('should render Line/Graph toggle and All Templates link', () => {
    renderLayout();

    const allTemplatesLink = screen.getByRole('link', { name: /All Templates/ });

    expect(screen.getByRole('button', { name: 'Line' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Graph' })).toBeInTheDocument();
    expect(allTemplatesLink).toBeInTheDocument();
    expect(allTemplatesLink).toHaveAttribute('href', ERoutes.Templates);
    expect(allTemplatesLink.querySelector('img')).toBeInTheDocument();
  });

  it('should switch store to graph view from the header toggle', () => {
    renderLayout();

    userEvent.click(screen.getByRole('button', { name: 'Graph' }));

    expect(mockDispatch).toHaveBeenCalledWith(setViewMode(EGraphViewMode.Graph));
  });

  it('should mark the layout as graph mode without page scroll lock class on line', () => {
    renderLayout();

    expect(document.querySelector('[data-test-id="template-layout"]')).toHaveAttribute('data-graph-mode', 'false');
    expect(document.body).not.toHaveClass('template-graph-lock');
  });

  it('should lock page scroll when graph mode is active', () => {
    const appContainer = document.createElement('div');
    appContainer.id = 'app-container';
    document.body.appendChild(appContainer);

    const { unmount } = renderLayout(EGraphViewMode.Graph);

    expect(document.querySelector('[data-test-id="template-layout"]')).toHaveAttribute('data-graph-mode', 'true');
    expect(document.body).toHaveClass('template-graph-lock');
    expect(appContainer).toHaveClass('template-graph-lock');

    unmount();
    expect(document.body).not.toHaveClass('template-graph-lock');
    expect(appContainer).not.toHaveClass('template-graph-lock');
    appContainer.remove();
  });

  it('should keep page scroll lock when a graph task is being edited', () => {
    const appContainer = document.createElement('div');
    appContainer.id = 'app-container';
    document.body.appendChild(appContainer);

    renderLayout(EGraphViewMode.Graph, 'task-1');

    expect(document.querySelector('[data-test-id="template-layout"]')).toHaveAttribute('data-graph-mode', 'true');
    expect(document.body).toHaveClass('template-graph-lock');
    expect(appContainer).toHaveClass('template-graph-lock');

    appContainer.remove();
  });
});
