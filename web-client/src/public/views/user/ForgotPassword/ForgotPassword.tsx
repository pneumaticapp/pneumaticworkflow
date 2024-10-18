import React, { useEffect } from 'react';
import { Formik, FormikConfig } from 'formik';
import { NavLink } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { IntlMessages } from '../../../components/IntlMessages';
import { TForgotPassword } from '../../../redux/actions';
import { validateEmail } from '../../../utils/validators';
import { Header, InputField, Button } from '../../../components/UI';

import styles from '../User.css';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { isEnvSignup } from '../../../constants/enviroment';

const INITIAL_VALUES_FORMIK: TForgotPasswordValues = {
  email: '',
};

export function ForgotPassword({ loading, sendForgotPassword }: IForgotPasswordProps) {
  const { formatMessage } = useIntl();

  useEffect(() => {
    document.title = TITLES.ForgotPassword;
  }, []);

  const handleSubmitForm: FormikConfig<TForgotPasswordValues>['onSubmit'] = (values) => {
    const { email } = values;

    sendForgotPassword({ email });
  };

  return (
    <>
      <Header size="4" tag="h2" className={styles['title']}>
        <IntlMessages id="user.password-forgot-title" />
      </Header>

      <Formik
        initialValues={INITIAL_VALUES_FORMIK}
        onSubmit={handleSubmitForm}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            email: validateEmail,
          });

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit, isValid, dirty }) => (
          <form className={styles['form']} onSubmit={handleSubmit}>
            <InputField
              name="email"
              title={formatMessage({ id: 'user.email' })}
              value={values.email}
              onChange={handleChange}
              errorMessage={errors.email}
              showErrorIfTouched
              containerClassName={styles['form__field']}
            />

            <Button
              type="submit"
              buttonStyle="yellow"
              isLoading={loading}
              className={styles['form__submit']}
              size="lg"
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
            <span>{formatMessage({ id: 'user.password-forgot-or' })}</span>
            <NavLink to={ERoutes.Register} className={styles['link']}>
              <IntlMessages id="user.register-link" />
            </NavLink>
          </>
        )}
      </div>
    </>
  );
}

export interface IForgotPasswordProps {
  loading?: boolean;
  sendForgotPassword(payload: TForgotPassword): void;
}

export type TForgotPasswordValues = {
  email: string;
};
