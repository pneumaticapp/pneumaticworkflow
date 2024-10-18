var enzyme = require('enzyme');
var Adapter = require('enzyme-adapter-react-16');
var { enMessages } = require('../src/public/lang/locales/en_US');
require('@testing-library/jest-dom');
require('@testing-library/jest-dom/extend-expect');

enzyme.configure({adapter: new Adapter() });

jest.mock('../src/public/redux/store.ts', () => ({
  store: {},
}))

jest.mock('../src/public/utils/analytics/utils.ts', () => ({
  getAnalyticsId: () => 'HACXziUYBTFoyfOSjcfaagk4DR5Gww6n',
  getAnalyticsPageParams: () => (['Main']),
}));

jest.mock('react-intl', () => {
  const reactIntl = jest.requireActual('react-intl');
  const defaultLocale = 'en-US';
  const locale = defaultLocale;
  const messages = enMessages;
  const intl = reactIntl.createIntl({ locale, defaultLocale, messages });

  return {
    ...reactIntl,
    useIntl: () => intl,
  };
});

jest.mock('../src/public/redux/store', () => {
  const state = {
    authUser: {
      isSuperuser: false,
    },
  };

  return {
    store: {
      getState: () => state,
    }
  }
});

jest.mock('react-redux', () => {
  return {
    connect: (mapStateToProps, mapDispatchToProps) => (ReactComponent) => ({
      mapStateToProps,
      mapDispatchToProps,
      ReactComponent
    }),
    Provider: ({ children }) => children,
    useDispatch: jest.fn(),
  }
});
