import React, { useEffect, useLayoutEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { Formik, Form, FormikConfig } from 'formik';

import {
  FIRST_DAY_OPTIONS,
  LANGUAGE_OPTIONS,
  TIMEZONE_OPTIONS,
  TIMEFORMAT_OPTIONS,
  DATEFORMAT_OPTIONS,
} from '../../constants/profile';
import { FormikInputField, InputField } from '../UI/Fields/InputField';
import { Button } from '../UI/Buttons/Button';
import { ESettingsTabs, TPasswordFields } from '../../types/profile';
import { TITLES } from '../../constants/titles';
import { IUpdateUserRequest } from '../../api/editProfile';
import { validateName, validatePhone } from '../../utils/validators';
import { getErrorsObject } from '../../utils/formik/getErrorsObject';
import { Header } from '../UI/Typeography/Header';
import { SectionTitle } from '../UI/Typeography/SectionTitle';
import { IAuthUser } from '../../types/redux';
import { FormikCheckbox } from '../UI/Fields/Checkbox';
import { AvatarController } from './AvatarController';
import { FormikDropdownList} from '../UI';
import { LockIcon } from '../icons/LockIcon';
import { ChangePassword } from './ChangePassword';

import styles from './Profile.css';

export interface IProfileProps {
  user: IAuthUser;
  editCurrentUser(body: IUpdateUserRequest): void;
  sendChangePassword(body: TPasswordFields): void;
  onChangeTab(tab: ESettingsTabs): void;
}

export type TProfileFields = {
  firstName: string;
  lastName: string;
  phone: string;
  isDigestSubscriber: boolean;
  isTasksDigestSubscriber: boolean;
  isCommentsMentionsSubscriber: boolean;
  isNewTasksSubscriber: boolean;
  isNewslettersSubscriber: boolean;
  isSpecialOffersSubscriber: boolean;
  language: string;
  timezone: string;
  dateFdw: string;
  timeformat: string;
  dateformat: string;
};

export function Profile({ user, editCurrentUser, sendChangePassword, onChangeTab }: IProfileProps) {
  const { formatMessage } = useIntl();
  const [isOpenModal, setIsOpenModal] = useState(false);
  const {
    id,
    email,
    firstName,
    lastName,
    phone,
    loading,
    isDigestSubscriber,
    isTasksDigestSubscriber,
    isCommentsMentionsSubscriber,
    isNewTasksSubscriber,
    isNewslettersSubscriber,
    isSpecialOffersSubscriber,
    language,
    timezone,
    dateFdw,
    dateFmt,
  } = user;
  const [monthFmt, yearFmt, timeFmt] = dateFmt.split(',');

  if (!id) return <div className="loading" />;

  const initialValues: TProfileFields = {
    firstName,
    lastName,
    phone: phone || '',
    isDigestSubscriber,
    isTasksDigestSubscriber,
    isCommentsMentionsSubscriber,
    isNewTasksSubscriber,
    isNewslettersSubscriber,
    isSpecialOffersSubscriber,
    language,
    timezone,
    dateFdw: String(dateFdw),
    timeformat: timeFmt.trim(),
    dateformat: `${monthFmt},${yearFmt},`,
  };

  const mapToFormatMessageOptions = (options: any) => {
    return options.map((item: any) => {
      return {
        ...item,
        label: formatMessage({ id: item.label }),
      };
    });
  };

  useEffect(() => {
    document.title = TITLES.Profile;
  }, []);

  useLayoutEffect(() => {
    onChangeTab(ESettingsTabs.Profile);
  }, []);

  const handleSubmit: FormikConfig<TProfileFields>['onSubmit'] = (values) => {
    const { dateformat, timeformat, ...userData } = values;
    editCurrentUser({ ...userData, dateFmt: `${dateformat} ${timeformat}` });
  };

  return (
    <div className={styles['profile-form']}>
      <Header className={styles['header']} size="4" tag="h1">
        {formatMessage({ id: 'user-info.title' })}
      </Header>

      <AvatarController user={user} containerClassname={styles['avatar-controller']} />

      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            firstName: validateName,
            lastName: validateName,
            phone: validatePhone,
          });

          return { ...errors };
        }}
      >
        <Form autoComplete="one-time-code">
          <fieldset className={styles['fields-group']}>
            <InputField
              value={id}
              fieldSize="lg"
              title={formatMessage({ id: 'user.id' })}
              disabled
              containerClassName={styles['field']}
            />
            <InputField
              value={email}
              fieldSize="lg"
              title={formatMessage({ id: 'user.email' })}
              disabled
              containerClassName={styles['field']}
              isRequired
            />
            <FormikInputField
              autoComplete="given-name"
              name="firstName"
              fieldSize="lg"
              title={formatMessage({ id: 'user.first-name' })}
              containerClassName={styles['field']}
              isRequired
            />
            <FormikInputField
              autoComplete="family-name"
              name="lastName"
              fieldSize="lg"
              title={formatMessage({ id: 'user.last-name' })}
              containerClassName={styles['field']}
              isRequired
            />
            <FormikInputField
              autoComplete="tel"
              name="phone"
              fieldSize="lg"
              title={formatMessage({ id: 'user.phone' })}
              containerClassName={styles['field']}
            />
          </fieldset>

          <fieldset className={styles['fields-group']}>
            <SectionTitle className={styles['fields-group__title']}>
              {formatMessage({ id: 'user-info.locale' })}
            </SectionTitle>

            <FormikDropdownList
              className={styles['field']}
              label={formatMessage({ id: 'user-info.locale.language' })}
              name="language"
              options={mapToFormatMessageOptions(LANGUAGE_OPTIONS)}
            />
            <FormikDropdownList
              label={formatMessage({ id: 'user-info.locale.timezone' })}
              className={styles['field']}
              name="timezone"
              options={mapToFormatMessageOptions(TIMEZONE_OPTIONS)}
            />
            <FormikDropdownList
              label={formatMessage({ id: 'user-info.locale.timeformat' })}
              className={styles['field']}
              name="timeformat"
              options={mapToFormatMessageOptions(TIMEFORMAT_OPTIONS)}
            />
            <FormikDropdownList
              label={formatMessage({ id: 'user-info.locale.dateformat' })}
              className={styles['field']}
              name="dateformat"
              options={mapToFormatMessageOptions(DATEFORMAT_OPTIONS)}
            />
            <FormikDropdownList
              label={formatMessage({ id: 'user-info.locale.dateFdw' })}
              className={styles['field']}
              name="dateFdw"
              options={mapToFormatMessageOptions(FIRST_DAY_OPTIONS)}
            />
          </fieldset>

          <fieldset className={styles['fields-group']}>
            <SectionTitle className={styles['fields-group__title']}>
              {formatMessage({ id: 'user-info.subscriptions' })}
            </SectionTitle>
            <FormikCheckbox
              title={formatMessage({ id: 'user-info.newsletter' })}
              name="isNewslettersSubscriber"
              containerClassName={styles['field']}
            />
            <FormikCheckbox
              title={formatMessage({ id: 'user-info.special-offers' })}
              name="isSpecialOffersSubscriber"
              containerClassName={styles['field']}
            />
            <FormikCheckbox
              title={formatMessage({ id: 'user-info.comments-and-mentions' })}
              name="isCommentsMentionsSubscriber"
              containerClassName={styles['field']}
            />
            <FormikCheckbox
              title={formatMessage({ id: 'user-info.new-tasks' })}
              name="isNewTasksSubscriber"
              containerClassName={styles['field']}
            />
            {user.isAdmin && (
              <FormikCheckbox
                title={formatMessage({ id: 'user-info.digest' })}
                name="isDigestSubscriber"
                containerClassName={styles['field']}
              />
            )}
            <FormikCheckbox
              title={formatMessage({ id: 'user-info.tasks-digest' })}
              name="isTasksDigestSubscriber"
              containerClassName={styles['field']}
            />
          </fieldset>

          <fieldset className={styles['fields-group']}>
            <SectionTitle className={styles['fields-group__title']}>
              {formatMessage({ id: 'user-info.change-password' })}
            </SectionTitle>

            <button type="button" className={styles['change-pass']} onClick={() => setIsOpenModal(true)}>
              <LockIcon></LockIcon>
              <p>Change your password</p>
            </button>
          </fieldset>

          <Button
            label={formatMessage({ id: 'user-info.change-submit' })}
            className={styles['submit-button']}
            isLoading={loading}
            type="submit"
            size="md"
            buttonStyle="yellow"
          />
        </Form>
      </Formik>
      <ChangePassword
        isOpen={isOpenModal}
        handleCloseModal={() => setIsOpenModal(false)}
        sendChangePassword={sendChangePassword}
        loading={loading}
      />
    </div>
  );
}
