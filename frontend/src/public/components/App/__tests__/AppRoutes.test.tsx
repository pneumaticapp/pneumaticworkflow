// <reference types="jest" />
import * as React from 'react';
import { render } from '@testing-library/react';
import { AppRoutes } from '../AppRoutes';
import { REDIRECT_URL_STORAGE_KEY } from '../../../constants/storageKeys';
import { ELoggedState } from '../../../types/redux';

// Mock react-redux
jest.mock('react-redux', () => ({
  useSelector: jest.fn(() => true),
}));

jest.mock('../../../utils/history', () => ({
  checkSomeRouteIsActive: jest.fn(() => false),
}));

// Mock routing components to just render a simple element and return props
jest.mock('react-router-dom', () => ({
  Route: () => <div data-testid="route" />,
  Switch: ({ children }: any) => <div data-testid="switch">{children}</div>,
  Redirect: (props: any) => <div data-testid="redirect" data-to={props.to} />,
}));

// Mock layout/view components that might cause issues during render
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
    // @ts-ignore
    delete window.location;
    window.location = {
      ...originalLocation,
      replace: jest.fn(),
    } as any;

    sessionStorage.clear();
    jest.clearAllMocks();
  });

  afterAll(() => {
    window.location = originalLocation;
  });

  const defaultUser = {
    id: 1,
    loggedState: ELoggedState.LoggedIn,
    isAdmin: false,
    isAccountOwner: false,
    account: { leaseLevel: 'tenant' },
  } as any;

  it('redirects to internal path via React Router Redirect', () => {
    // arrange
    sessionStorage.setItem(REDIRECT_URL_STORAGE_KEY, '/tasks/123');

    // act
    const { getByTestId } = render(
      <AppRoutes containerClassnames="test-class" user={defaultUser} />
    );

    // assert
    expect(window.location.replace).not.toHaveBeenCalled();
    const redirect = getByTestId('redirect');
    expect(redirect.getAttribute('data-to')).toBe('/tasks/123');
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
  });

  it('calls window.location.replace for external URL and renders routes', () => {
    // arrange
    sessionStorage.setItem(
      REDIRECT_URL_STORAGE_KEY,
      'https://pneumatic.app/files/abc-123',
    );

    // act
    const { getByTestId } = render(
      <AppRoutes containerClassnames="test-class" user={defaultUser} />,
    );

    // assert
    expect(window.location.replace).toHaveBeenCalledWith(
      'https://pneumatic.app/files/abc-123',
    );
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
    // Must render normal routes (not blank page) for file downloads
    // where the browser stays on the current page
    expect(getByTestId('switch')).toBeTruthy();
  });

  it('redirects to localhost URL via window.location.replace', () => {
    // arrange
    sessionStorage.setItem(
      REDIRECT_URL_STORAGE_KEY,
      'http://localhost/files/abc-123',
    );

    // act
    render(<AppRoutes containerClassnames="test-class" user={defaultUser} />);

    // assert
    expect(window.location.replace).toHaveBeenCalledWith(
      'http://localhost/files/abc-123',
    );
    expect(sessionStorage.getItem(REDIRECT_URL_STORAGE_KEY)).toBe('');
  });
});
