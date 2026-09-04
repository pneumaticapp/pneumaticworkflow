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
import { TAccountLeaseLevel } from '../../types/user';
import { ESubscriptionPlan } from '../../types/account';

import styles from './ProfileAccount.css';

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

const EMPTY_UPLOADED_FILES: TUploadedFile[] = [];

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
  const { formatMessage } = useIntl();
  const savedState: TEditableFields = { name, logoSm, logoLg };
  const [state, changeState] = React.useState<TEditableFields>(savedState);
  const savedStateRef = React.useRef(savedState);
  const hasNoData = !accountId && !name;

  React.useEffect(() => {
    document.title = TITLES.AccountSettings;
  }, []);
  React.useLayoutEffect(() => {
    onChangeTab(ESettingsTabs.AccountSettings);
  }, []);

  // Account data is hydrated after the first render and refreshed after every save
  if (isContentChanged(savedStateRef.current, savedState)) {
    savedStateRef.current = savedState;
    changeState(savedState);
  }

  const isDirty = isContentChanged(savedState, state) && isValidState(state);

  const logoSmFiles = React.useMemo(
    () => (state.logoSm ? [getFileByUrl(state.logoSm)] : EMPTY_UPLOADED_FILES),
    [state.logoSm],
  );
  const logoLgFiles = React.useMemo(
    () => (state.logoLg ? [getFileByUrl(state.logoLg)] : EMPTY_UPLOADED_FILES),
    [state.logoLg],
  );

  const changeField = (field: keyof TEditableFields) => (value: TEditableFields[keyof TEditableFields]) => {
    changeState((prevState) => ({ ...prevState, [field]: value }));
  };

  const handleLogoSmFiles = React.useCallback((files: TUploadedFile[]) => {
    changeState((prevState) => ({ ...prevState, logoSm: getUrlByFile(files[0]) }));
  }, []);

  const handleLogoLgFiles = React.useCallback((files: TUploadedFile[]) => {
    changeState((prevState) => ({ ...prevState, logoLg: getUrlByFile(files[0]) }));
  }, []);

  const handleSubmit = () => editCurrentAccount(state);

  if (hasNoData) {
    return loading ? <div className="loading" /> : null;
  }

  return (
    <div className={styles['settings-form']}>
      <Header className={styles['header']} size="4" tag="h1">
        {formatMessage({ id: 'user-account.company-settings' })}
      </Header>

      <div className={styles['fields-group']}>
        <InputField
          title={formatMessage({ id: 'user.company-name' })}
          value={state.name}
          onChange={(e) => changeField('name')(e.currentTarget.value)}
          errorMessage={validateCompanyName(state.name)}
          disabled={!isAdmin}
          containerClassName={styles['field']}
        />
      </div>

      {leaseLevel !== 'tenant' && billingPlan && (
        <div className={styles['fields-group']}>
          <SectionTitle className={styles['fields-group__title']}>
            {formatMessage({ id: 'user-info.personalization' })}
          </SectionTitle>

          <AttachmentField
            key={`logo-sm-${accountId}`}
            title={formatMessage({ id: 'user-info.logo-sm' })}
            accountId={accountId!}
            uploadedFiles={logoSmFiles}
            setUploadedFiles={handleLogoSmFiles}
            description={formatMessage({ id: 'user-info.logo-sm-desc' })}
            containerClassName={styles['field']}
            acceptedType="image"
            expectedImageWidth={80}
            expectedImageHeight={80}
          />

          <AttachmentField
            key={`logo-lg-${accountId}`}
            title={formatMessage({ id: 'user-info.logo-lg' })}
            accountId={accountId!}
            uploadedFiles={logoLgFiles}
            setUploadedFiles={handleLogoLgFiles}
            description={formatMessage({ id: 'user-info.logo-lg-desc' })}
            containerClassName={styles['field']}
            acceptedType="image"
            expectedImageWidth={340}
            expectedImageHeight={96}
          />
        </div>
      )}

      {isAdmin && (
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
      )}
    </div>
  );
}

export type TEditableFields = Pick<IProfileAccountProps, 'name' | 'logoSm' | 'logoLg'>;

function isContentChanged(initialState: TEditableFields, state: TEditableFields) {
  const initialValues = Object.values(initialState);

  return Object.values(state).some((value, index) => value !== initialValues[index]);
}

function isValidState({ name }: TEditableFields) {
  return !validateCompanyName(name);
}

const getFileByUrl = (url: string): TUploadedFile => {
  return {
    id: url,
    url,
    thumbnailUrl: url,
    name: '',
    size: 0,
  };
};

const getUrlByFile = (file?: TUploadedFile): string | null => {
  if (!file || file.isRemoved) {
    return null;
  }

  return file.url;
};
