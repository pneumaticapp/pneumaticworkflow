import * as ReactDOM from 'react-dom';
import { within } from '@testing-library/react';

jest.mock('../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({ api: { urls: {} } }),
  getBrowserConfig: () => ({
    invitedUser: {},
  }),
}));
jest.mock('../redux/store');
jest.mock('../components/App', () => ({ AppContainer: () => 'AppContainer stub' }));
jest.mock('redux-persist/integration/react', () => ({
  PersistGate: ({ children }: { children: unknown }) => children,
}));

describe('browser entry point', () => {
  let rootElement: HTMLDivElement;

  beforeEach(() => {
    rootElement = document.createElement('div');
    rootElement.id = 'pneumatic-frontend';
    document.body.appendChild(rootElement);
  });

  afterEach(() => {
    ReactDOM.unmountComponentAtNode(rootElement);
    rootElement.remove();
  });

  it('renders the app inside the container with id pneumatic-frontend', () => {
    jest.requireActual('../browser');

    expect(within(rootElement).getByText('AppContainer stub')).toBeInTheDocument();
  });
});
