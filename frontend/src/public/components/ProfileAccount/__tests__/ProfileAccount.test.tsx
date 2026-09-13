import * as React from 'react';
import { act, fireEvent, render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../lang/locales/en_US';
import { ESubscriptionPlan } from '../../../types/account';
import { TUploadedFile } from '../../../utils/uploadFiles';
import { AttachmentField, IAttachmentFieldProps } from '../../UI/Fields/AttachmentField';
import { IProfileAccountProps, ProfileAccount } from '../ProfileAccount';

jest.mock('../../UI/Fields/AttachmentField', () => ({
  AttachmentField: jest.fn(() => null),
}));

const attachmentFieldMock = AttachmentField as unknown as jest.Mock;
const getLogoProps = (expectedImageWidth: number) =>
  [...attachmentFieldMock.mock.calls]
    .reverse()
    .find(([props]) => props.expectedImageWidth === expectedImageWidth)?.[0] as IAttachmentFieldProps;

const defaultProps: IProfileAccountProps = {
  accountId: 1,
  name: 'Acme',
  logoSm: 'https://example.com/old-small.png',
  logoLg: 'https://example.com/old-large.png',
  loading: false,
  leaseLevel: 'standard',
  billingPlan: ESubscriptionPlan.Premium,
  isAdmin: true,
  editCurrentAccount: jest.fn(),
  onChangeTab: jest.fn(),
};

const getMarkup = (props: Partial<IProfileAccountProps> = {}) => (
  <IntlProvider locale="en" messages={enMessages}>
    <ProfileAccount {...defaultProps} {...props} />
  </IntlProvider>
);

const renderProfileAccount = (props: Partial<IProfileAccountProps> = {}) => render(getMarkup(props));

const uploadedLogo: TUploadedFile = {
  id: 'new-logo',
  name: 'new-logo.png',
  size: 100,
  url: 'https://example.com/new-logo.png',
  thumbnailUrl: 'https://example.com/new-logo.png',
};

describe('ProfileAccount', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it.each([
    ['small', 80],
    ['large', 340],
  ])('updates the %s logo preview before the form is saved', (_, expectedImageWidth) => {
    renderProfileAccount();

    act(() => getLogoProps(expectedImageWidth).setUploadedFiles([uploadedLogo]));

    expect(getLogoProps(expectedImageWidth).uploadedFiles[0]?.url).toBe(uploadedLogo.url);

    act(() => getLogoProps(expectedImageWidth).setUploadedFiles([{ ...uploadedLogo, isRemoved: true }]));

    expect(getLogoProps(expectedImageWidth).uploadedFiles).toEqual([]);
  });

  it('shows saved logos after account data arrives', () => {
    const { rerender } = renderProfileAccount({
      accountId: undefined,
      name: '',
      logoSm: null,
      logoLg: null,
      loading: true,
    });

    expect(attachmentFieldMock).not.toHaveBeenCalled();

    rerender(getMarkup());

    expect(getLogoProps(80).uploadedFiles[0]?.url).toBe(defaultProps.logoSm);
    expect(getLogoProps(340).uploadedFiles[0]?.url).toBe(defaultProps.logoLg);
  });

  it('keeps the uploaded logo after an unrelated field change', () => {
    const { getByDisplayValue } = renderProfileAccount();

    act(() => getLogoProps(80).setUploadedFiles([uploadedLogo]));

    fireEvent.change(getByDisplayValue('Acme'), { target: { value: 'Acme Inc' } });

    expect(getLogoProps(80).uploadedFiles[0]?.url).toBe(uploadedLogo.url);
  });

  it('disables the submit button once the saved logo comes back from the server', () => {
    const savedLogoUrl = 'https://cdn.example.com/new-logo.png';
    const { getByRole, rerender } = renderProfileAccount();

    act(() => getLogoProps(80).setUploadedFiles([uploadedLogo]));

    expect(getByRole('button', { name: 'Save changes' })).toBeEnabled();

    rerender(getMarkup({ logoSm: savedLogoUrl }));

    expect(getByRole('button', { name: 'Save changes' })).toBeDisabled();
    expect(getLogoProps(80).uploadedFiles[0]?.url).toBe(savedLogoUrl);
  });
});
