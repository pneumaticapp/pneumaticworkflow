import * as React from 'react';
import { act, fireEvent, render } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../lang/locales/en_US';
import { ESubscriptionPlan } from '../../../types/account';
import { TUploadedFile } from '../../../utils/uploadFiles';
import { AttachmentField, IAttachmentFieldProps } from '../../UI/Fields/AttachmentField';
import { ProfileAccount } from '../ProfileAccount';

jest.mock('../../UI/Fields/AttachmentField', () => ({
  AttachmentField: jest.fn(() => null),
}));

const attachmentFieldMock = AttachmentField as unknown as jest.Mock;
const getLogoProps = (expectedImageWidth: number) => (
  [...attachmentFieldMock.mock.calls]
    .reverse()
    .find(([props]) => props.expectedImageWidth === expectedImageWidth)?.[0] as IAttachmentFieldProps
);

const renderProfileAccount = () => render(
  <IntlProvider locale="en" messages={enMessages}>
    <ProfileAccount
      accountId={1}
      name="Acme"
      logoSm="https://example.com/old-small.png"
      logoLg="https://example.com/old-large.png"
      loading={false}
      leaseLevel="standard"
      billingPlan={ESubscriptionPlan.Premium}
      isAdmin
      editCurrentAccount={jest.fn()}
      onChangeTab={jest.fn()}
    />
  </IntlProvider>,
);

describe('ProfileAccount', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it.each([
    ['small', 80],
    ['large', 340],
  ])('updates the %s logo preview before the form is saved', (_, expectedImageWidth) => {
    const uploadedLogo: TUploadedFile = {
      id: 'new-logo',
      name: 'new-logo.png',
      size: 100,
      url: 'https://example.com/new-logo.png',
      thumbnailUrl: 'https://example.com/new-logo.png',
    };

    renderProfileAccount();

    act(() => getLogoProps(expectedImageWidth).setUploadedFiles([uploadedLogo]));

    expect(getLogoProps(expectedImageWidth).uploadedFiles[0]?.url).toBe(uploadedLogo.url);

    act(() => getLogoProps(expectedImageWidth).setUploadedFiles([{ ...uploadedLogo, isRemoved: true }]));

    expect(getLogoProps(expectedImageWidth).uploadedFiles).toEqual([]);
  });

  it('shows saved logos after account data arrives', () => {
    const { rerender } = render(
      <IntlProvider locale="en" messages={enMessages}>
        <ProfileAccount
          name=""
          logoSm={null}
          logoLg={null}
          loading
          leaseLevel="standard"
          billingPlan={ESubscriptionPlan.Premium}
          isAdmin
          editCurrentAccount={jest.fn()}
          onChangeTab={jest.fn()}
        />
      </IntlProvider>,
    );

    expect(attachmentFieldMock).not.toHaveBeenCalled();

    rerender(
      <IntlProvider locale="en" messages={enMessages}>
        <ProfileAccount
          accountId={1}
          name="Acme"
          logoSm="https://example.com/old-small.png"
          logoLg="https://example.com/old-large.png"
          loading={false}
          leaseLevel="standard"
          billingPlan={ESubscriptionPlan.Premium}
          isAdmin
          editCurrentAccount={jest.fn()}
          onChangeTab={jest.fn()}
        />
      </IntlProvider>,
    );

    expect(getLogoProps(80).uploadedFiles[0]?.url).toBe('https://example.com/old-small.png');
    expect(getLogoProps(340).uploadedFiles[0]?.url).toBe('https://example.com/old-large.png');
  });

  it('keeps the uploaded logo after an unrelated field change', () => {
    const uploadedLogo: TUploadedFile = {
      id: 'new-logo',
      name: 'new-logo.png',
      size: 100,
      url: 'https://example.com/new-logo.png',
      thumbnailUrl: 'https://example.com/new-logo.png',
    };

    const { getByDisplayValue } = renderProfileAccount();

    act(() => getLogoProps(80).setUploadedFiles([uploadedLogo]));

    fireEvent.change(getByDisplayValue('Acme'), { target: { value: 'Acme Inc' } });

    expect(getLogoProps(80).uploadedFiles[0]?.url).toBe(uploadedLogo.url);
  });
});
