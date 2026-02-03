import React, { useMemo } from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';

import { BaseModal, ModalHeader, ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { InputField } from '../../../UI/Fields/InputField';
import { DropdownList } from '../../../UI/DropdownList';
import { Button } from '../../../UI/Buttons/Button';
import { validateEmail, validateRegistrationPassword } from '../../../../utils/validators';
import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { copyToClipboard } from '../../../../utils/helpers';
import { createPassword } from '../../../../utils/createPassword';
import { NotificationManager } from '../../../UI/Notifications';

import { ICreateUserModalProps, ICreateUserFormData, IStatusOption } from './types';

import styles from './CreateUserModal.css';

const formatStatusOption = (
  { label, value } : IStatusOption,
  { context }: { context: string },
  selectedValue: IStatusOption['value'],
) => {
  if (context === 'menu' && value === selectedValue) {
    return <span className={styles['modal__option--selected']}>{label}</span>;
  }
  return label;
};

export function CreateUserModal({ isOpen, onClose }: ICreateUserModalProps) {
  const { formatMessage } = useIntl();

  const statusOptions: IStatusOption[] = [
    { label: formatMessage({ id: 'team.create-user-modal.status-admin' }), value: 'Admin' },
    { label: formatMessage({ id: 'team.create-user-modal.status-user' }), value: 'User' },
  ];

  const initialValues: ICreateUserFormData = useMemo(
    () => ({
      firstName: '',
      lastName: '',
      email: '',
      status: 'User',
      password: createPassword(),
    }),
    [isOpen],
  );

  const handleSubmit = (values: ICreateUserFormData) => {
    console.log('Create User:', values);
  };

  return (
    <BaseModal isOpen={isOpen} toggle={onClose}>
      <ModalHeader toggle={onClose}>
        {formatMessage({ id: 'team.create-user-modal.title' })}
      </ModalHeader>

      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            email: validateEmail,
            password: validateRegistrationPassword,
          });

          return errors;
        }}
      >
        {({ values, errors, handleChange, handleSubmit: formikSubmit, setFieldValue, isValid, dirty }) => {
          const handleStatusChange = (option: IStatusOption) => setFieldValue('status', option.value);
          
          const renderStatusOption = (option: IStatusOption, { context }: { context: string }) =>
            formatStatusOption(option, { context }, values.status);

          return (
            <form onSubmit={formikSubmit}>
              <ModalBody>
                <div className={styles['modal__form']}>
                  <InputField
                    name="firstName"
                    value={values.firstName}
                    onChange={handleChange}
                    title={formatMessage({ id: 'team.create-user-modal.first-name' })}
                    fieldSize="lg"
                  />
                  <InputField
                    name="lastName"
                    value={values.lastName}
                    onChange={handleChange}
                    title={formatMessage({ id: 'team.create-user-modal.last-name' })}
                    fieldSize="lg"
                  />
                  <InputField
                    name="email"
                    value={values.email}
                    onChange={handleChange}
                    title={formatMessage({ id: 'team.create-user-modal.email' })}
                    fieldSize="lg"
                    isRequired
                    type="email"
                    errorMessage={errors.email}
                    showErrorIfTouched
                  />

                  <DropdownList
                    label={formatMessage({ id: 'team.create-user-modal.status' })}
                    options={statusOptions}
                    value={statusOptions.find((opt) => opt.value === values.status)}
                    onChange={handleStatusChange}
                    className={styles['modal__dropdown--required']}
                    formatOptionLabel={renderStatusOption}
                  />

                  <div className={styles['modal__password-field']}>
                    <InputField
                      name="password"
                      value={values.password}
                      onChange={handleChange}
                      title={formatMessage({ id: 'team.create-user-modal.password' })}
                      fieldSize="lg"
                      type="text"
                      isRequired
                      errorMessage={errors.password}
                      showErrorIfTouched
                    />
                    <button
                      type="button"
                      className={styles['modal__copy-btn']}
                      onClick={() => {
                        copyToClipboard(values.password);
                        NotificationManager.success({ message: 'team.create-user-modal.password-copied' });
                      }}
                    >
                      {formatMessage({ id: 'team.create-user-modal.copy' })}
                    </button>
                  </div>
                </div>
              </ModalBody>

              <ModalFooter>
                <Button
                  type="submit"
                  label={formatMessage({ id: 'team.create-user-modal.submit' })}
                  buttonStyle="yellow"
                  disabled={!isValid || !dirty}
                />
              </ModalFooter>
            </form>
          );
        }}
      </Formik>
    </BaseModal>
  );
}
