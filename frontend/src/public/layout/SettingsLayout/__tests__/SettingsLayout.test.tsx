// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { intlMock } from '../../../__stubs__/intlMock';
import { ESettingsTabs } from '../../../types/profile';
import { ERoutes } from '../../../constants/routes';
import { history } from '../../../utils/history';
import { SettingsLayoutComponent } from '../SettingsLayout';

jest.mock('../../../components/TopNav', () => ({
  TopNavContainer: ({ leftContent }: { leftContent: React.ReactNode }) => <nav>{leftContent}</nav>,
}));
jest.mock('../../../components/Dashboard/DashboardWidgets', () => ({ DashboardWidgets: () => null }));
jest.mock('../../../components/UI', () => ({
  Tabs: ({ values, onChange }: { values: { id: string; label: string }[]; onChange: (id: string) => void }) => (
    <div>
      {values.map(({ id, label }) => (
        <button key={id} onClick={() => onChange(id)}>
          {label}
        </button>
      ))}
    </div>
  ),
}));
jest.mock('../../../api/mcp', () => ({ isMcpEnabled: () => true }));
jest.mock('../../../utils/history', () => ({ history: { location: { pathname: '/' } } }));

describe('SettingsLayout', () => {
  const t = (id: string) => intlMock.formatMessage({ id });
  const CONNECTIONS = t('mcp.connections.title');
  const onChangeTab = jest.fn();
  const layout = () => (
    <SettingsLayoutComponent activeTab={ESettingsTabs.Profile} onChangeTab={onChangeTab}>
      <div />
    </SettingsLayoutComponent>
  );

  beforeEach(() => {
    jest.clearAllMocks();
    history.location.pathname = ERoutes.Profile;
  });

  it('показывает вход в подключения MCP в меню настроек', () => {
    // arrange
    // act
    render(layout());

    // assert
    expect(screen.getByRole('link', { name: CONNECTIONS })).toHaveAttribute('href', ERoutes.McpConnections);
  });

  it('передаёт выбор вкладки существующему обработчику', () => {
    // arrange
    render(layout());

    // act
    userEvent.click(screen.getByRole('button', { name: 'Settings' }));

    // assert
    expect(onChangeTab).toHaveBeenCalledWith(ESettingsTabs.AccountSettings);
  });

  it('убирает меню настроек при переходе на другой маршрут', () => {
    // arrange
    const { rerender } = render(layout());

    // act
    history.location.pathname = '/tasks/';
    rerender(layout());

    // assert
    expect(screen.queryByRole('link', { name: CONNECTIONS })).not.toBeInTheDocument();
  });
});
