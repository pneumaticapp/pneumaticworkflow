import * as React from 'react';
import { useEffect, useLayoutEffect, useState } from 'react';
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
import { TUserListItem } from '../../types/user';
import { FormikCheckbox } from '../UI/Fields/Checkbox';
import { AvatarController } from './AvatarController';
import { FormikDropdownList } from '../UI';
import { LockIcon } from '../icons/LockIcon';
import { ChangePassword } from './ChangePassword';
import { ProfileVacationFields } from './ProfileVacationFields';

import styles from './Profile.css';

const arraysEqual = (a: number[], b: number[]) =>
  a.length === b.length && a.every((v, i) => v === b[i]);

export interface IProfileProps {
  user: IAuthUser;
  editCurrentUser(body: IUpdateUserRequest): void;
  sendChangePassword(body: TPasswordFields): void;
  onChangeTab(tab: ESettingsTabs): void;
  onVacationActivate(data: {
    substituteUserIds: number[];
    vacationStartDate: string | null;
    vacationEndDate: string | null;
    absenceStatus?: string;
  }): void;
  onVacationDeactivate(): void;
  availableUsers: TUserListItem[];
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
  absenceStatus: string;
  vacationStartDate: string | null;
  vacationEndDate: string | null;
  substituteUserIds: number[];
};



export function Profile({
  user,
  editCurrentUser,
  sendChangePassword,
  onChangeTab,
  onVacationActivate,
  onVacationDeactivate,
  availableUsers,
}: IProfileProps) {
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
    absenceStatus: user.isAbsent ? (user.absenceStatus || 'vacation') : 'active',
    vacationStartDate: user.vacationStartDate || null,
    vacationEndDate: user.vacationEndDate || null,
    substituteUserIds: user.substituteUserIds || [],
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
    const { dateformat, timeformat, absenceStatus, vacationStartDate, vacationEndDate, substituteUserIds, ...userData } = values;
    editCurrentUser({ ...userData, dateFmt: `${dateformat} ${timeformat}` });

    const prevIsAbsent = user.isAbsent || false;
    const nextIsAbsent = absenceStatus !== 'active';
    
    // Determine if any vacation fields have changed
    const prevAbsenceStatus = user.isAbsent ? (user.absenceStatus || 'vacation') : 'active';
    const vacationSettingsChanged =
      absenceStatus !== prevAbsenceStatus ||
      vacationStartDate !== (user.vacationStartDate || null) ||
      vacationEndDate !== (user.vacationEndDate || null) ||
      !arraysEqual(substituteUserIds, user.substituteUserIds || []);
      
    if (vacationSettingsChanged) {
      if (nextIsAbsent) {
        onVacationActivate({
          substituteUserIds,
          vacationStartDate,
          vacationEndDate,
          absenceStatus,
        });
      } else if (prevIsAbsent && !nextIsAbsent) {
        onVacationDeactivate();
      }
    }
  };

  return (
    <div className={styles['profile-form']}>
      <Header className={styles['header']} size="4" tag="h1">
        {formatMessage({ id: 'user-info.title' })}
      </Header>

      <AvatarController user={user} containerClassname={styles['avatar-controller']} />

      <Formik
        enableReinitialize
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            firstName: validateName,
            lastName: validateName,
            phone: validatePhone,
          });

          if (values.absenceStatus !== 'active' && (!values.substituteUserIds || values.substituteUserIds.length === 0)) {
            errors.substituteUserIds = formatMessage({ id: 'validation.required' });
          }

          if (
            values.absenceStatus !== 'active' &&
            values.vacationStartDate &&
            values.vacationEndDate &&
            values.vacationEndDate < values.vacationStartDate
          ) {
            errors.vacationEndDate = formatMessage({ id: 'user-info.vacation.end-date-before-start' });
          }

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

          <ProfileVacationFields availableUsers={availableUsers} />

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
              <p>{formatMessage({ id: 'user-info.change-your-password' })}</p>
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
