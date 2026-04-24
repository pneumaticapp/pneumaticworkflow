import * as React from 'react';
import { useMemo } from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { BaseModal, ModalHeader, ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { Button } from '../../../UI/Buttons/Button';
import { validateEmail, validateRegistrationPassword } from '../../../../utils/validators';
import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { copyToClipboard } from '../../../../utils/helpers';
import { createPassword } from '../../../../utils/createPassword';
import { NotificationManager } from '../../../UI/Notifications';
import { createUser } from '../../../../redux/accounts/slice';

import { ICreateUserModalProps, IStatusOption, EUserRole, ICreateUserFormValues } from './types';

import styles from './CreateUserModal.css';

const formatStatusOption = (
  { label, value }: IStatusOption,
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
  const dispatch = useDispatch();

  const statusOptions: IStatusOption[] = [
    { label: formatMessage({ id: 'team.create-user-modal.status-admin' }), value: EUserRole.Admin },
    { label: formatMessage({ id: 'team.create-user-modal.status-user' }), value: EUserRole.User },
  ];

  const initialValues: ICreateUserFormValues = useMemo(
    () => ({
      firstName: '',
      lastName: '',
      email: '',
      role: EUserRole.User,
      password: createPassword(),
    }),
    [isOpen],
  );

  const handleSubmit = (values: ICreateUserFormValues) => {
    const { role, ...userData } = values;
    dispatch(createUser({ ...userData, isAdmin: role === EUserRole.Admin }));
  };

  return (
    <BaseModal isOpen={isOpen} toggle={onClose}>
      <ModalHeader toggle={onClose}>
        <span data-testid="create-user-modal-header">
          {formatMessage({ id: 'team.create-user-modal.title' })}
        </span>
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
        {({ values, handleSubmit: formikSubmit, isValid, dirty }) => {
          const currentStatusValue = values.role;
          const renderStatusOption = (option: IStatusOption, { context }: { context: string }) =>
            formatStatusOption(option, { context }, currentStatusValue);

          return (
            <form onSubmit={formikSubmit}>
              <ModalBody>
                <div className={styles['modal__form']}>
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

                  <FormikDropdownList
                    name="role"
                    label={formatMessage({ id: 'team.create-user-modal.status' })}
                    options={statusOptions}
                    className={styles['modal__dropdown--required']}
                    formatOptionLabel={renderStatusOption}
                  />

                  <div className={styles['modal__password-field']}>
                    <FormikInputField
                      name="password"
                      title={formatMessage({ id: 'team.create-user-modal.password' })}
                      fieldSize="lg"
                      type="text"
                      isRequired
                      containerClassName={`${styles['modal__input-ellipsis']} ${styles['modal__password-input-wrap']}`}
                    />
                    <button
                      type="button"
                      className={styles['modal__copy-btn']}
                      onClick={() => {
                        copyToClipboard(values.password || '');
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
