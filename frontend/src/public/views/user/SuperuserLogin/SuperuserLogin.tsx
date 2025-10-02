import React, { useEffect } from 'react';
import { Formik, FormikConfig } from 'formik';
import { useIntl } from 'react-intl';

import { TITLES } from '../../../constants/titles';
import { IntlMessages } from '../../../components/IntlMessages';
import { validateEmail } from '../../../utils/validators';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { Header, Button, InputField } from '../../../components/UI';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';

import styles from '../User.css';
import { TLoginSuperuserPayload } from '../../../redux/actions';

const INITIAL_VALUES_FORMIK: TSuperuserLoginValues = {
  email: '',
};

export function SuperuserLogin({ isSuperuser, loading, loginSuperuser }: ISuperuserLoginProps) {
  const { formatMessage } = useIntl();

  useEffect(() => {
    document.title = TITLES.SuperuserLogin;

    if (!isSuperuser) {
      history.replace(ERoutes.Main);
    }
  }, []);

  const handleSubmitForm: FormikConfig<TSuperuserLoginValues>['onSubmit'] = (values) => {
    const { email } = values;

    loginSuperuser({ email });
  };

  return (
    <div className="form-side">
      <Header size="4" tag="p" className={styles['title']}>
        <IntlMessages id="user.superuser-login-title" />
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
              containerClassName={styles['form-field']}
            />

            <Button
              buttonStyle="yellow"
              isLoading={loading}
              className={styles['form__submit']}
              size="lg"
              type="submit"
              disabled={!isValid || !dirty}
              label={formatMessage({ id: 'user.login-button' })}
            />
          </form>
        )}
      </Formik>
    </div>
  );
}

export interface ISuperuserLoginProps {
  isSuperuser?: boolean;
  loading?: boolean;
  hasError?: boolean;
  loginSuperuser(payload: TLoginSuperuserPayload): void;
}

export type TSuperuserLoginValues = {
  email: string;
};
