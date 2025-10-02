import React, { useEffect, useState } from 'react';
import { Formik, FormikConfig } from 'formik';
import { NavLink } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { confirmResetPassword, EResetPasswordStatus } from '../../../api/confirmResetPassword';
import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { getQueryStringParams, history } from '../../../utils/history';
import { IConfirmResetPassword } from '../../../redux/actions';
import { IntlMessages } from '../../../components/IntlMessages';
import { NotificationManager } from '../../../components/UI/Notifications';
import { UNKNOWN_ERROR } from '../../../utils/getErrorMessage';
import { validatePassword } from '../../../utils/validators';
import { Header, InputField, Button } from '../../../components/UI';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';

import styles from '../User.css';
import { isEnvSignup } from '../../../constants/enviroment';

const MAP_STATUS_ERRORS: { [key in EResetPasswordStatus]: string } = {
  [EResetPasswordStatus.Valid]: '',
  [EResetPasswordStatus.Expired]: 'user.password-reset-expired',
  [EResetPasswordStatus.Invalid]: 'user.password-reset-invalid',
};

const INITIAL_VALUES_FORMIK: TResetPasswordValues = {
  newPassword: '',
  confirmNewPassword: '',
};

export function ResetPassword({ loading, sendResetPassword }: IResetPasswordProps) {
  const { formatMessage } = useIntl();

  const [tokenLocal, setTokenLocal] = useState('');

  useEffect(() => {
    document.title = TITLES.ResetPassword;
  }, []);

  useEffect(() => {
    const getToken = async () => {
      const { token } = getQueryStringParams(history.location.search);
      const statusResponse = token && (await confirmResetPassword(token));

      if (!statusResponse || statusResponse.status !== EResetPasswordStatus.Valid) {
        history.replace(ERoutes.ForgotPassword);
        const message = (statusResponse && MAP_STATUS_ERRORS[statusResponse.status]) || UNKNOWN_ERROR;
        NotificationManager.warning({ message });

        return;
      }

      setTokenLocal(token);
    };

    getToken();
  }, []);

  const handleSubmitForm: FormikConfig<TResetPasswordValues>['onSubmit'] = (values) => {
    const { newPassword, confirmNewPassword } = values;

    sendResetPassword({ newPassword, confirmNewPassword, token: tokenLocal });
  };

  return (
    <div className="form-side">
      <Header size="4" tag="p" className={styles['title']}>
        <IntlMessages id="user.password-reset-title" />
      </Header>

      <Formik
        initialValues={INITIAL_VALUES_FORMIK}
        onSubmit={handleSubmitForm}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            newPassword: validatePassword,
            confirmNewPassword: validatePassword,
          });

          if (values.newPassword !== values.confirmNewPassword) {
            errors.newPassword = 'validation.passwords-dont-match';
            errors.confirmNewPassword = 'validation.passwords-dont-match';
          }

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit}>
            <InputField
              name="newPassword"
              type="password"
              value={values.newPassword}
              onChange={handleChange}
              title={formatMessage({ id: 'user.new-password' })}
              errorMessage={errors.newPassword}
              containerClassName={styles['form__field']}
              showErrorIfTouched
              showPasswordVisibilityToggle
            />

            <InputField
              name="confirmNewPassword"
              type="password"
              value={values.confirmNewPassword}
              onChange={handleChange}
              title={formatMessage({ id: 'user.new-password-again' })}
              errorMessage={errors.confirmNewPassword}
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
              label={formatMessage({ id: 'user.password-forgot-button' })}
            />
          </form>
        )}
      </Formik>

      <div className={styles['footnote']}>
        <NavLink to={ERoutes.Login} className={styles['link']}>
          <IntlMessages id="user.login-link" />
        </NavLink>
        {isEnvSignup && (
          <>
            <span>or</span>
            <NavLink to={ERoutes.Register} className={styles['link']}>
              <IntlMessages id="user.register-link" />
            </NavLink>
          </>
        )}
      </div>
    </div>
  );
}
export interface IResetPasswordProps {
  loading?: boolean;
  sendResetPassword(payload: IConfirmResetPassword): void;
}

export type TResetPasswordValues = {
  newPassword: string;
  confirmNewPassword: string;
};
