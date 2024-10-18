import * as React from 'react';
import { useIntl } from 'react-intl';

import { TITLES } from '../../constants/titles';
import { IUpdateAccountRequest } from '../../api/editAccount';
import { validateCompanyName } from '../../utils/validators';
import { InputField } from '../UI/Fields/InputField';
import { Button } from '../UI/Buttons/Button';
import { Header } from '../UI/Typeography/Header';
import { ESettingsTabs } from '../../types/profile';
import { AttachmentField, SectionTitle } from '../UI';
import { TUploadedFile } from '../../utils/uploadFiles';

import styles from './ProfileAccount.css';
import { TAccountLeaseLevel } from '../../types/user';
import { ESubscriptionPlan } from '../../types/account';

export interface IProfileAccountProps {
  accountId?: number;
  name: string;
  logoSm: string | null;
  logoLg: string | null;
  loading: boolean;
  leaseLevel: TAccountLeaseLevel;
  billingPlan: ESubscriptionPlan;
  isAdmin?: boolean;
  editCurrentAccount(body: IUpdateAccountRequest): void;
  onChangeTab(tab: ESettingsTabs): void;
}

export function ProfileAccount({
  accountId,
  name,
  logoSm,
  logoLg,
  loading,
  isAdmin,
  leaseLevel,
  billingPlan,
  onChangeTab,
  editCurrentAccount,
}: IProfileAccountProps) {
  const hasNoData = !accountId && !name;

  const { formatMessage } = useIntl();

  if (hasNoData) {
    return loading ? <div className="loading" /> : null;
  }
  const initialState: TEditableFields = { name, logoSm, logoLg };
  const [state, changeState] = React.useState(initialState);
  const [isDirty, changeDirty] = React.useState(false);

  React.useEffect(() => {
    document.title = TITLES.AccountSettings;
  }, []);
  React.useLayoutEffect(() => {
    onChangeTab(ESettingsTabs.AccountSettings);
  }, []);
  React.useEffect(() => {
    changeDirty(false);
  }, [name, logoSm, logoLg]);

  const changeField = (field: keyof TEditableFields) => (value: TEditableFields[keyof TEditableFields]) => {
    const newState = { ...state, [field]: value };
    changeState(newState);
    changeDirty(isContentChanged(initialState, newState) && isValidState(newState));
  };

  const handleSubmit = () => editCurrentAccount(state);

  return (
    <div className={styles['settings-form']}>
      <Header className={styles['header']} size="4" tag="h1">
        {formatMessage({ id: 'user-account.company-settings' })}
      </Header>

      <div className={styles['fields-group']}>
        <InputField
          title={formatMessage({ id: 'user.company-name' })}
          value={state.name}
          onChange={e => changeField('name')(e.currentTarget.value)}
          errorMessage={validateCompanyName(state.name)}
          disabled={!isAdmin}
          containerClassName={styles['field']}
        />
      </div>

      {(leaseLevel !== 'tenant' &&
        billingPlan &&
        billingPlan !== ESubscriptionPlan.Free) && (
        <div className={styles['fields-group']}>
          <SectionTitle className={styles['fields-group__title']}>
            {formatMessage({ id: 'user-info.personalization' })}
          </SectionTitle>

          <AttachmentField
            title={formatMessage({ id: 'user-info.logo-sm' })}
            accountId={accountId!}
            uploadedFiles={logoSm ? [getFileByUrl(logoSm)] : []}
            setUploadedFiles={files => changeField('logoSm')(getUrlByFile(files[0]))}
            description={formatMessage({ id: 'user-info.logo-sm-desc' })}
            containerClassName={styles['field']}
            acceptedType="image"
            expectedImageWidth={80}
            expectedImageHeight={80}
          />

          <AttachmentField
            title={formatMessage({ id: 'user-info.logo-lg' })}
            accountId={accountId!}
            uploadedFiles={logoLg ? [getFileByUrl(logoLg)] : []}
            setUploadedFiles={files => changeField('logoLg')(getUrlByFile(files[0]))}
            description={formatMessage({ id: 'user-info.logo-lg-desc' })}
            containerClassName={styles['field']}
            acceptedType="image"
            expectedImageWidth={340}
            expectedImageHeight={96}
          />
        </div>
      )}

      {isAdmin &&
        <Button
          disabled={!isDirty}
          label={formatMessage({ id: 'user-info.change-submit' })}
          isLoading={loading}
          type="submit"
          size="md"
          onClick={handleSubmit}
          buttonStyle="yellow"
          className={styles['submit-button']}
        />
      }
    </div>
  );
}

export type TEditableFields = Pick<IProfileAccountProps, 'name' | 'logoSm' | 'logoLg'>;

function isContentChanged(initialState: TEditableFields, state: TEditableFields) {
  const initialValues = Object.values(initialState);

  return Object.values(state).some((value, index) => value !== initialValues[index]);
}

function isValidState({ name }: TEditableFields) {
  return !(
    validateCompanyName(name)
  );
}

const getFileByUrl = (url: string): TUploadedFile => {
  return {
    id: -1,
    url,
    thumbnailUrl: url,
    name: '',
    size: 0,
  };
}

const getUrlByFile = (file?: TUploadedFile): string | null => {
  if (!file || file.isRemoved) {
    return null;
  }

  return file.url;
}
