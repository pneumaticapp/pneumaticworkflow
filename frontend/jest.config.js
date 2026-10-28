module.exports = {
  collectCoverage: false,
  collectCoverageFrom: [
    'src/**/*.{ts,tsx,js,jsx}',
    '!src/**/index.{ts,tsx,js,jsx}',
    '!src/**/*.d.{ts,tsx}',
    '!src/**/*.config.js',
    '!src/**/(__tests__|tests|__storybook__|__mocks__|__stubs__)/*.{ts,tsx,js,jsx}',
    '!src/public/assets/**/*.{ts,tsx,js,jsx}',
  ],
  moduleDirectories: ['node_modules'],
  coverageDirectory: 'artifacts',
  setupFilesAfterEnv: ['<rootDir>/jest/jest.setup.js'],
  snapshotSerializers: ['enzyme-to-json/serializer'],
  // Type checking is already covered by `npm run eslint` and fork-ts-checker in the
  // webpack build, so ts-jest only transpiles here. A full TS program per worker
  // costs ~500 MB of baseline heap and is the main source of OOM on large runs.
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true }],
    '.+\\.(css|styl|less|sass|scss)$': 'jest-css-modules-transform',
    '\\.(svg|png|jpg|woff2|woff|eot|ttf)$': '<rootDir>/jest/file-preprocessor.js',
  },
  transformIgnorePatterns: ['/node_modules/(?!(\\S+\\.css))', '/node_modules/(?!(\\S+\\.js))'],
  testMatch: ['<rootDir>/src/**/__tests__/**/*.test.(ts|tsx|js|jsx)', '<rootDir>/tests/**/*.test.(ts|tsx|js|jsx)'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  modulePaths: ['jest'],
  modulePathIgnorePatterns: ['promise-polyfill/*'],
  moduleNameMapper: {
    '^uuid$': '<rootDir>/node_modules/exceljs/node_modules/uuid/dist/index.js',
    '.scss$': 'empty-stub.js',
    'react-perfect-scrollbar/dist/css/styles.css': 'empty-stub.js',
    'rc-switch/assets/index.css': 'empty-stub.js',
    'rc-slider/assets/index.css': 'empty-stub.js',
    'promise-polyfill/src/polyfill': 'empty-stub.js',
    'react-datepicker/dist/react-datepicker.css': 'empty-stub.js',
    'assets/css/library/.+\\.css$': 'empty-stub.js',
    'draft-js/dist/Draft.css': 'empty-stub.js',
    'style.css': 'empty-stub.js',
    'react-phone-number-input/style.css': 'empty-stub.js',
    'redux-persist/es/constants': 'empty-stub.js',
    'react-inner-image-zoom/lib/InnerImageZoom/styles.min.css': 'empty-stub.js',
  },
  testEnvironmentOptions: { url: 'http://localhost' },
  testEnvironment: 'jest-environment-jsdom',
  // Every worker is a separate Node process with its own jsdom, so an unbounded
  // worker pool exhausts RAM on developer machines. The idle limit recycles a
  // worker once its heap grows past the threshold instead of leaking until OOM.
  maxWorkers: '50%',
  workerIdleMemoryLimit: '512MB',
  clearMocks: true,
};
