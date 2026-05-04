import * as React from 'react';
import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useFormikContext } from 'formik';
import classNames from 'classnames';

import { DateField } from '../UI/Fields/DateField';
import { UsersDropdown } from '../UI/form/UsersDropdown';
import { UserPerformer, EBgColorTypes } from '../UI/UserPerformer';
import { ETaskPerformerType } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { FormikDropdownList } from '../UI';
import { SectionTitle } from '../UI/Typeography/SectionTitle';

import { formatDateLocal } from '../../utils/formatDateLocal';
import { useSubstituteUsers } from '../../utils/useSubstituteUsers';

import styles from './Profile.css';

const NOOP = () => {};

interface IProfileVacationFieldsProps {
  availableUsers: TUserListItem[];
}

export type TProfileVacationValues = {
  absenceStatus: string;
  vacationStartDate: string | null;
  vacationEndDate: string | null;
  substituteUserIds: number[];
};

export function ProfileVacationFields({ availableUsers }: IProfileVacationFieldsProps) {
  const { values, setFieldValue, errors, submitCount } = useFormikContext<TProfileVacationValues>();
  const { formatMessage } = useIntl();
  const [dateError, setDateError] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (values.absenceStatus !== 'active' && !values.vacationStartDate) {
      setFieldValue('vacationStartDate', formatDateLocal(new Date()));
    }
  }, [values.absenceStatus, values.vacationStartDate, setFieldValue]);

  const STATUS_OPTIONS = [
    { value: 'active', label: formatMessage({ id: 'user-info.vacation.type.active', defaultMessage: 'Active' }) },
    { value: 'vacation', label: formatMessage({ id: 'user-info.vacation.type.vacation' }) },
    { value: 'sick_leave', label: formatMessage({ id: 'user-info.vacation.type.sick-leave' }) },
  ];

  const onSubstituteChange = (nextIds: number[]) => {
    setFieldValue('substituteUserIds', nextIds);
  };

  const {
    mapUserOptions,
    selectedUserOptions,
    handleAddUser,
    handleRemoveUser,
  } = useSubstituteUsers(availableUsers, values.substituteUserIds, onSubstituteChange);

  const validateDates = (start: string | null, end: string | null): boolean => {
    if (start && end && end < start) {
      setDateError(formatMessage({ id: 'user-info.vacation.end-date-before-start' }));
      return false;
    }
    setDateError(undefined);
    return true;
  };

  const handleStartDateChange = (date: Date | null) => {
    const formatted = formatDateLocal(date);
    setFieldValue('vacationStartDate', formatted);
    validateDates(formatted, values.vacationEndDate);
  };

  const handleEndDateChange = (date: Date | null) => {
    const formatted = formatDateLocal(date);
    setFieldValue('vacationEndDate', formatted);
    validateDates(values.vacationStartDate, formatted);
  };

  return (
    <fieldset className={styles['fields-group']}>
      <SectionTitle className={styles['fields-group__title']}>
        {formatMessage({ id: 'user-info.vacation.title' })}
      </SectionTitle>

      <FormikDropdownList
        label={formatMessage({ id: 'user-info.vacation.status', defaultMessage: 'Options' })}
        className={styles['field']}
        name="absenceStatus"
        options={STATUS_OPTIONS}
      />

      {values.absenceStatus !== 'active' && (
        <>
          <div className={classNames(styles['field'], styles['dates-row'])}>
            <DateField
              value={values.vacationStartDate}
              onChange={handleStartDateChange}
              fieldSize="lg"
              title={formatMessage({ id: 'user-info.vacation.start-date' })}
            />
            <DateField
              value={values.vacationEndDate}
              onChange={handleEndDateChange}
              fieldSize="lg"
              title={formatMessage({ id: 'user-info.vacation.end-date' })}
              errorMessage={dateError}
            />
          </div>

          <div className={styles['field']}>
            <UsersDropdown
              label={formatMessage({ id: 'user-info.vacation.substitutes' })}
              isMulti
              controlSize="lg"
              options={mapUserOptions}
              value={selectedUserOptions}
              onChange={handleAddUser}
              onChangeSelected={handleRemoveUser}
              isSearchable
              placeholder={formatMessage({ id: 'user-info.vacation.substitutes' })}
              inviteLabel=""
              onClickInvite={NOOP}
              isRequired
              errorMessage={submitCount > 0 && errors.substituteUserIds ? String(errors.substituteUserIds) : undefined}
            />
            {selectedUserOptions.length > 0 && (
              <div className={styles['selected-users']}>
                {selectedUserOptions.map((opt) => (
                  <UserPerformer
                    key={opt.id}
                    user={{ ...opt, type: ETaskPerformerType.User }}
                    bgColor={EBgColorTypes.Light}
                    onClick={() => handleRemoveUser(opt)}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </fieldset>
  );
}
