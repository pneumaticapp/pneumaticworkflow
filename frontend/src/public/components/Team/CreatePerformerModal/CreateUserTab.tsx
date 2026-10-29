import React, { useState } from 'react';
import classnames from 'classnames';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { ModalBody, ModalFooter } from '../../UI/BaseModal';
import { FormikInputField } from '../../UI/Fields/InputField';
import { FormikSelect } from '../../UI/Select';
import { Button } from '../../UI/Buttons/Button';
import { validateEmail, validateRegistrationPassword } from '../../../utils/validators';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { copyToClipboard } from '../../../utils/helpers';
import { createPassword } from '../../../utils/createPassword';
import { NotificationManager } from '../../UI/Notifications';
import { createUser } from '../../../redux/accounts/slice';
import { getTeamCreatePerformerModalIsSubmitting } from '../../../redux/selectors/team';

import type { ICreatePerformerTabProps, ICreateUserFormValues, IStatusOption } from './types';
import { EUserRole } from './types';

import modalStyles from '../PerformerModal.css';
import styles from './CreatePerformerModal.css';

const formatStatusOption = (
  { label, value }: IStatusOption,
  { context }: { context: string },
  selectedValue: IStatusOption['value'],
) => {
  if (context === 'menu' && value === selectedValue) {
    return <span className={styles['modal__option_selected']}>{label}</span>;
  }
  return label;
};

export function CreateUserTab({ isVisible }: ICreatePerformerTabProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isSubmitting = useSelector(getTeamCreatePerformerModalIsSubmitting);

  const statusOptions: IStatusOption[] = [
    { label: formatMessage({ id: 'team.create-user-modal.status-admin' }), value: EUserRole.Admin },
    { label: formatMessage({ id: 'team.create-user-modal.status-user' }), value: EUserRole.User },
  ];

  const [initialValues] = useState<ICreateUserFormValues>(() => ({
    firstName: '',
    lastName: '',
    email: '',
    role: EUserRole.User,
    password: createPassword(),
  }));

  const validateForm = (values: ICreateUserFormValues) =>
    getErrorsObject(values, {
      email: validateEmail,
      password: validateRegistrationPassword,
    });

  const handleSubmit = (values: ICreateUserFormValues) => {
    const { role, ...userData } = values;
    dispatch(createUser({ ...userData, isAdmin: role === EUserRole.Admin }));
  };

  const handleCopyPassword = (password: string) => {
    copyToClipboard(password);
    NotificationManager.success({ message: 'team.create-user-modal.password-copied' });
  };

  return (
    <Formik
      initialValues={initialValues}
      initialErrors={validateForm(initialValues)}
      validate={validateForm}
      onSubmit={handleSubmit}
    >
      {({ values, handleSubmit: formikSubmit, isValid, dirty }) => {
        if (!isVisible) return null;

        const currentStatusValue = values.role;
        const renderStatusOption = (option: IStatusOption, { context }: { context: string }) =>
          formatStatusOption(option, { context }, currentStatusValue);

        return (
          <form onSubmit={formikSubmit}>
            <ModalBody className={modalStyles['performer-modal__body']}>
              <div className={modalStyles['performer-modal__form']}>
                <FormikInputField
                  name="firstName"
                  title={formatMessage({ id: 'team.create-user-modal.first-name' })}
                  fieldSize="lg"
                  containerClassName={styles['modal__input-ellipsis']}
                />
                <FormikInputField
                  name="lastName"
                  title={formatMessage({ id: 'team.create-user-modal.last-name' })}
                  fieldSize="lg"
                  containerClassName={styles['modal__input-ellipsis']}
                />
                <FormikInputField
                  name="email"
                  title={formatMessage({ id: 'team.create-user-modal.email' })}
                  fieldSize="lg"
                  isRequired
                  type="email"
                  containerClassName={styles['modal__input-ellipsis']}
                />

                <FormikSelect
                  name="role"
                  label={formatMessage({ id: 'team.create-user-modal.status' })}
                  options={statusOptions}
                  isRequired
                  formatOptionLabel={renderStatusOption}
                />

                <div className={styles['modal__password-field']}>
                  <FormikInputField
                    name="password"
                    title={formatMessage({ id: 'team.create-user-modal.password' })}
                    fieldSize="lg"
                    type="text"
                    isRequired
                    containerClassName={classnames(
                      styles['modal__input-ellipsis'],
                      styles['modal__password-input-wrap'],
                    )}
                  />
                  <button
                    type="button"
                    className={styles['modal__copy-btn']}
                    onClick={() => handleCopyPassword(values.password || '')}
                  >
                    {formatMessage({ id: 'team.create-user-modal.copy' })}
                  </button>
                </div>
              </div>
            </ModalBody>

            <ModalFooter className={modalStyles['performer-modal__footer']}>
              <Button
                className={modalStyles['performer-modal__submit']}
                type="submit"
                label={formatMessage({ id: 'team.create-user-modal.submit' })}
                buttonStyle="yellow"
                disabled={!isValid || !dirty || isSubmitting}
                isLoading={isSubmitting}
              />
            </ModalFooter>
          </form>
        );
      }}
    </Formik>
  );
}
