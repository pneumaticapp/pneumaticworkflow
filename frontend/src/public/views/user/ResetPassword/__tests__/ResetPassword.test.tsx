import * as React from 'react';
import { render, waitFor } from '@testing-library/react';

import { ResetPassword } from '../ResetPassword';
import { ERoutes } from '../../../../constants/routes';

jest.mock('../../../../utils/logger', () => ({
  logger: {
    error: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock('../../../../api/confirmResetPassword', () => ({
  confirmResetPassword: jest.fn(),
  EResetPasswordStatus: {
    Valid: 0,
    Expired: 1,
    Invalid: 2,
  },
}));

jest.mock('../../../../utils/history', () => ({
  history: {
    location: { search: '?token=test-token-123' },
    replace: jest.fn(),
  },
  getQueryStringParams: jest.fn(() => ({ token: 'test-token-123' })),
}));

jest.mock('../../../../components/UI/Notifications', () => ({
  NotificationManager: {
    notifyApiError: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock('../../../../utils/getErrorMessage', () => ({
  getErrorMessage: jest.fn((error: { message?: string }) => error?.message || 'Error message'),
  UNKNOWN_ERROR: 'Something Went Wrong',
}));

jest.mock('react-router-dom', () => ({
  NavLink: ({ children }: { children?: React.ReactNode }) => <span>{children}</span>,
}));

jest.mock('../../../../components/IntlMessages', () => ({
  IntlMessages: ({ id }: { id: string }) => <span>{id}</span>,
}));

jest.mock('../../../../components/UI', () => ({
  Header: ({ children }: { children?: React.ReactNode }) => <h1>{children}</h1>,
  InputField: ({
    name,
    title,
    errorMessage,
    onChange,
    value,
    type,
  }: {
    name: string;
    title: string;
    errorMessage?: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    value: string;
    type: string;
  }) => (
    <div>
      <label htmlFor={name}>{title}</label>
      <input id={name} name={name} type={type} value={value} onChange={onChange} />
      {errorMessage && <span>{errorMessage}</span>}
    </div>
  ),
  Button: ({
    label,
    isLoading,
    disabled,
    type,
  }: {
    label: string;
    isLoading?: boolean;
    disabled?: boolean;
    type?: 'submit' | 'button';
  }) => (
    <button type={type} disabled={disabled || isLoading}>
      {label}
    </button>
  ),
}));

const { confirmResetPassword, EResetPasswordStatus } = require('../../../../api/confirmResetPassword');
const { logger } = require('../../../../utils/logger');
const { history } = require('../../../../utils/history');
const { NotificationManager } = require('../../../../components/UI/Notifications');
const { getErrorMessage } = require('../../../../utils/getErrorMessage');

describe('ResetPassword', () => {
  const mockSendResetPassword = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles confirmResetPassword failure by logging error, notifying user and redirecting to ForgotPassword', async () => {
    const mockApiError = new Error('Invalid or expired reset token');
    confirmResetPassword.mockRejectedValueOnce(mockApiError);

    render(<ResetPassword sendResetPassword={mockSendResetPassword} />);

    await waitFor(() => {
      expect(logger.error).toHaveBeenCalledTimes(1);
    });

    expect(logger.error).toHaveBeenCalledWith(mockApiError);
    expect(getErrorMessage).toHaveBeenCalledTimes(1);
    expect(getErrorMessage).toHaveBeenCalledWith(mockApiError);
    expect(NotificationManager.notifyApiError).toHaveBeenCalledTimes(1);
    expect(NotificationManager.notifyApiError).toHaveBeenCalledWith(mockApiError, {
      message: 'Invalid or expired reset token',
    });
    expect(history.replace).toHaveBeenCalledTimes(1);
    expect(history.replace).toHaveBeenCalledWith(ERoutes.ForgotPassword);
  });

  it('does not log error or redirect when reset token is valid', async () => {
    confirmResetPassword.mockResolvedValueOnce({ status: EResetPasswordStatus.Valid });

    render(<ResetPassword sendResetPassword={mockSendResetPassword} />);

    await waitFor(() => {
      expect(confirmResetPassword).toHaveBeenCalledTimes(1);
    });

    expect(confirmResetPassword).toHaveBeenCalledWith('test-token-123');
    expect(logger.error).not.toHaveBeenCalled();
    expect(NotificationManager.notifyApiError).not.toHaveBeenCalled();
    expect(history.replace).not.toHaveBeenCalled();
  });
});
