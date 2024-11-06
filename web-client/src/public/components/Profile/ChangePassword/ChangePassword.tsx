import React from 'react';
import { useIntl } from 'react-intl';
import { Formik, Form, FormikConfig } from 'formik';

import { Button, FormikInputField, Modal } from '../../UI';
import { validateNewPassword, validateOldPassword } from '../validators';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';

import styles from './ChangePassword.css';

export type TChangePasswordFields = {
  oldPassword: string;
  confirmNewPassword: string;
  newPassword: string;
};

export function ChangePassword({ isOpen, handleCloseModal, sendChangePassword, loading }: any) {
  const { formatMessage } = useIntl();

  const initialValues: TChangePasswordFields = {
    confirmNewPassword: '',
    newPassword: '',
    oldPassword: '',
  };

  const handleSubmit: FormikConfig<TChangePasswordFields>['onSubmit'] = (values) => {
    const { oldPassword, newPassword, confirmNewPassword } = values;
    const isPasswordChanged = newPassword && confirmNewPassword && oldPassword;
    if (isPasswordChanged) {
      sendChangePassword({ oldPassword, newPassword, confirmNewPassword });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validate={(values) => {
          const { oldPassword, newPassword, confirmNewPassword } = values;

          const passwordErrors = getErrorsObject(values, {
            oldPassword: validateOldPassword,
            newPassword: validateNewPassword,
          });

          if (oldPassword === newPassword) {
            passwordErrors.newPassword = 'validation.passwords-are-same';
          }

          if (newPassword !== confirmNewPassword) {
            passwordErrors.confirmNewPassword = 'validation.passwords-dont-match';
          }

          return { ...passwordErrors };
        }}
      >
        <Form>
          <header className={styles['change-pass__header']}>
            <h1 className={styles['change-pass__title']}>{formatMessage({ id: 'user-info.change-your-password' })}</h1>
          </header>
          <fieldset className={styles['fields-group']}>
            <FormikInputField
              autoComplete="current-password"
              type="password"
              name="oldPassword"
              fieldSize="lg"
              title={formatMessage({ id: 'user.old-password' })}
              containerClassName={styles['field']}
            />
            <FormikInputField
              autoComplete="new-password"
              type="password"
              name="newPassword"
              fieldSize="lg"
              title={formatMessage({ id: 'user.new-password' })}
              containerClassName={styles['field']}
            />
            <FormikInputField
              autoComplete="new-password"
              type="password"
              name="confirmNewPassword"
              fieldSize="lg"
              title={formatMessage({ id: 'user.new-password-again' })}
              containerClassName={styles['field']}
            />
          </fieldset>
          <footer className={styles['change-pass__footer']}>
            <Button
              label={formatMessage({ id: 'user-info.change-your-password.confirm' })}
              className={styles['submit-button']}
              isLoading={loading}
              type="submit"
              size="md"
              buttonStyle="yellow"
            />
            <Button
              label={formatMessage({ id: 'user-info.change-your-password.cancel' })}
              className="cancel-button"
              type="button"
              size="md"
              onClick={handleCloseModal}
              buttonStyle='transparent-yellow'
            />
          </footer>
        </Form>
      </Formik>
    </Modal>
  );
}
