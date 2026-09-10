import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { FieldsetUsageBanner } from '../FieldsetUsageBanner';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { history } from '../../../../../utils/history';
import { getTemplateEditRoute } from '../../../../../utils/routes';
import { DropdownList } from '../../../../UI/DropdownList';

jest.mock('../../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../../utils/routes', () => ({
  getTemplateEditRoute: jest.fn((id: number) => `/templates/edit/${id}`),
}));

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, className }: { children: React.ReactNode; to: string; className?: string }) =>
    React.createElement('a', { href: to, className }, children),
}));

jest.mock('../../../../UI', () => ({
  Tooltip: jest.fn(({ children }: { children: React.ReactNode }) => children),
}));

jest.mock('../../../../UI/DropdownList', () => ({
  DropdownList: jest.fn(() => null),
}));

function requireJestMock(value: unknown, label: string): jest.Mock {
  if (!jest.isMockFunction(value)) {
    throw new Error(`${label} is not a jest.Mock`);
  }
  return value;
}

const formatMsg = (id: string, values?: Record<string, string | number>) =>
  intlMock.formatMessage({ id }, values);

type TDropdownOption = {
  value: string;
  onClick: () => void;
  label: React.ReactNode;
};

const getDropdownOptions = (): TDropdownOption[] => {
  const mock = requireJestMock(DropdownList, 'DropdownList');
  if (mock.mock.calls.length === 0) {
    throw new Error('DropdownList was not rendered');
  }
  return mock.mock.calls[0][0].options as TDropdownOption[];
};

describe('FieldsetUsageBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('when usage is empty', () => {
    it('renders not-linked text', () => {
      render(React.createElement(FieldsetUsageBanner, { usage: [] }));

      expect(screen.getByText(formatMsg('fieldsets.usage.not-linked'))).toBeInTheDocument();
    });

    it('does not render DropdownList', () => {
      render(React.createElement(FieldsetUsageBanner, { usage: [] }));

      expect(DropdownList).not.toHaveBeenCalled();
    });
  });

  describe('when usage contains templates', () => {
    const usage = [
      { id: 5, name: 'Template Alpha' },
      { id: 12, name: 'Template Beta' },
    ];

    it('renders linked text with template count', () => {
      render(React.createElement(FieldsetUsageBanner, { usage }));

      expect(
        screen.getByText(formatMsg('fieldsets.usage.linked', { count: 2 })),
      ).toBeInTheDocument();
    });

    it('passes options with template names to DropdownList', () => {
      render(React.createElement(FieldsetUsageBanner, { usage }));

      const options = getDropdownOptions();

      expect(options).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ value: 'Template Alpha' }),
          expect.objectContaining({ value: 'Template Beta' }),
        ]),
      );
      expect(options).toHaveLength(2);
    });

    it('calls history.push with template route on option click', () => {
      render(React.createElement(FieldsetUsageBanner, { usage }));

      const options = getDropdownOptions();
      const alphaOption = options.find((o) => o.value === 'Template Alpha');
      if (!alphaOption) throw new Error('Option "Template Alpha" not found');

      alphaOption.onClick();

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(getTemplateEditRoute(5));
    });
  });
});
