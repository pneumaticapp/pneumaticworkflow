import * as React from 'react';
import { render } from '@testing-library/react';
import { AppRoutes } from '../AppRoutes';
import { REDIRECT_URL_STORAGE_KEY } from '../../../constants/storageKeys';
import { ELoggedState } from '../../../types/redux';
import { getBrowserConfigEnv } from '../../../utils/getConfig';

jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn(() => ({ api: { fileServiceUrl: 'https://pneumatic.app/files' }, featureFlags: {} })),
}));
jest.mock('../../Mcp/McpConnect', () => ({ McpConnect: () => <div /> }));
jest.mock('../../Mcp/McpConnections', () => ({ McpConnections: () => <div /> }));
jest.mock('../../Mcp/McpUpload', () => ({ McpUpload: () => <div /> }));

jest.mock('react-redux', () => ({
  connect: () => (ReactComponent: unknown) => ReactComponent,
  Provider: ({ children }: { children: React.ReactNode }) => children,
  useDispatch: jest.fn(),
  useSelector: jest.fn(() => true),
}));

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(() => false),
}));

jest.mock('react-router-dom', () => ({
  Route: () => <div data-testid="route" />,
  Switch: ({ children }: any) => <div data-testid="switch">{children}</div>,
  Redirect: (props: any) => <div data-testid="redirect" data-to={props.to} />,
}));

jest.mock('../../ProtectedRoute', () => ({
  ProtectedRoute: () => <div data-testid="protected-route" />,
}));
jest.mock('../../../layout', () => ({
  MainLayout: () => <div data-testid="main-layout" />,
}));
jest.mock('../../../views/Error', () => ({ Error: () => <div /> }));
jest.mock('../../../views/Main', () => ({ Main: () => <div /> }));
jest.mock('../../../views/Workflows', () => ({ WorkflowsView: () => <div /> }));
jest.mock('../../../views/Highlights', () => ({ HighlightsView: () => <div /> }));
jest.mock('../../../views/Settings', () => ({ Settings: () => <div /> }));
jest.mock('../../../views/Tasks', () => ({ TasksView: () => <div /> }));
jest.mock('../../../views/Team', () => ({ TeamView: () => <div /> }));
jest.mock('../../../views/user', () => ({ User: () => <div /> }));
jest.mock('../../../views/Templates', () => ({ TemplatesView: () => <div /> }));
jest.mock('../../../views/Template', () => ({ TemplateView: () => <div /> }));
jest.mock('../../../views/Integrations', () => ({ IntegrationsView: () => <div /> }));
jest.mock('../../../views/IntegrationDetails', () => ({ IntegrationDetailsView: () => <div /> }));
jest.mock('../../../views/Tenants', () => ({ TenantsView: () => <div /> }));
jest.mock('../../../views/Datasets', () => ({ DatasetsView: () => <div /> }));
jest.mock('../../GuestTask', () => ({ GuestTask: () => <div /> }));
jest.mock('../../CollectPaymentDetails', () => ({ CollectPaymentDetails: () => <div /> }));
jest.mock('../../AfterPaymentDetailsProvided', () => ({ AfterPaymentDetailsProvided: () => <div /> }));

describe('AppRoutes Redirect Logic', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        replace: jest.fn(),
      },
    });

    sessionStorage.clear();
    jest.clearAllMocks();
  });

  afterAll(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  const defaultUser = {
    id: 1,
    loggedState: ELoggedState.LoggedIn,
    isAdmin: false,
    isAccountOwner: false,
    account: { leaseLevel: 'tenant' },
  } as any;

  it('redirects to internal path via React Router Redirect', () => {
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, '/tasks/123');

    const { getByTestId } = render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);

    expect(window.location.replace).not.toHaveBeenCalled();
    const redirect = getByTestId('redirect');
    expect(redirect.getAttribute('data-to')).toBe('/tasks/123');
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
  });

  it('calls window.location.replace for external URL and renders routes', () => {
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, 'https://pneumatic.app/files/abc-123');

    const { getByTestId } = render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);

    expect(window.location.replace).toHaveBeenCalledWith('https://pneumatic.app/files/abc-123');
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
    expect(getByTestId('switch')).toBeTruthy();
  });

  it('redirects to localhost URL via window.location.replace', () => {
    (getBrowserConfigEnv as jest.Mock).mockReturnValueOnce({
      api: { fileServiceUrl: 'http://localhost/files' },
      featureFlags: {},
    });
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, 'http://localhost/files/abc-123');

    render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);

    expect(window.location.replace).toHaveBeenCalledWith('http://localhost/files/abc-123');
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
  });

  it('blocks an arbitrary external URL from login storage', () => {
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, 'https://evil.example');
    render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);
    expect(window.location.replace).not.toHaveBeenCalled();
  });

  it('returns through Express for the MCP consent continuation', () => {
    const target = '/mcp/connect?request_id=550e8400-e29b-41d4-a716-446655440000&step=consent';
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, target);
    render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);
    expect(window.location.replace).toHaveBeenCalledWith(target);
  });
});
