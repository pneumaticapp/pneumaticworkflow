import React, { useEffect } from 'react';
import { Formik, FormikConfig } from 'formik';
import { useIntl } from 'react-intl';
import moment from 'moment-timezone';

import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { history } from '../../../utils/history';
import { IntlMessages } from '../../../components/IntlMessages';
import { NavLink } from '../../../components/NavLink';
import { NotificationManager } from '../../../components/UI/Notifications';
import { TUserInvited } from '../../../types/user';
import { validateName, validateRegistrationPassword } from '../../../utils/validators';
import { Button, Header, InputField } from '../../../components/UI';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { TIMEZONE_OFFSET_MAP } from '../../../constants/profile';

import styles from '../User.css';

export interface IRegisterInviteProps {
  loading?: boolean;
  id: string;
  registerUserInvited(payload: TUserInvited): void;
}

export type TRegisterInviteValues = {
  firstName: string;
  lastName: string;
  password: string;
};

const INITIAL_VALUES_FORMIK: TRegisterInviteValues = {
  firstName: '',
  lastName: '',
  password: '',
};

export function RegisterInvite({ loading, id, registerUserInvited }: IRegisterInviteProps) {
  const { formatMessage } = useIntl();
  const defaultOffset = moment().utcOffset();

  useEffect(() => {
    document.title = TITLES.Register;
  }, []);

  useEffect(() => {
    if (!id) {
      NotificationManager.warning({ message: 'user.invite-invalid-token' });
      history.replace(ERoutes.Login);
    }
  }, [id]);

  const handleSubmitForm: FormikConfig<TRegisterInviteValues>['onSubmit'] = (values) => {
    const { firstName, lastName, password } = values;

    registerUserInvited({ firstName, lastName, password, timezone: TIMEZONE_OFFSET_MAP[defaultOffset] });
  };

  return (
    <>
      <Header size="4" tag="p" className={styles['title']}>
        <IntlMessages id="user.register-title-invite-pre" />
      </Header>

      <Formik
        initialValues={INITIAL_VALUES_FORMIK}
        onSubmit={handleSubmitForm}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            firstName: validateName,
            lastName: validateName,
            password: validateRegistrationPassword,
          });

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit} autoComplete="off">
            <InputField
              name="firstName"
              value={values.firstName}
              onChange={handleChange}
              title={formatMessage({ id: 'user.first-name' })}
              errorMessage={errors.firstName}
              data-test-id="input-user-first-name"
              containerClassName={styles['form__field']}
              showErrorIfTouched
            />
            <InputField
              name="lastName"
              value={values.lastName}
              onChange={handleChange}
              title={formatMessage({ id: 'user.last-name' })}
              errorMessage={errors.lastName}
              data-test-id="input-user-last-name"
              containerClassName={styles['form__field']}
              showErrorIfTouched
            />
            <InputField
              name="password"
              value={values.password}
              onChange={handleChange}
              errorMessage={errors.password}
              title={formatMessage({ id: 'user.password' })}
              data-test-id="input-registration-password"
              containerClassName={styles['form__field']}
              showErrorIfTouched
              showPasswordVisibilityToggle
            />

            <Button
              buttonStyle="yellow"
              isLoading={loading}
              className={styles['form__submit']}
              size="lg"
              type="submit"
              disabled={!isValid || !dirty}
              label={formatMessage({ id: 'user.register-button' })}
            />

            <div className={styles['footnote']}>
              <IntlMessages id="user.register-already" />

              <NavLink to={ERoutes.Login} className={styles['link']}>
                <IntlMessages id="user.login-link" />
              </NavLink>
            </div>
          </form>
        )}
      </Formik>
    </>
  );
}
