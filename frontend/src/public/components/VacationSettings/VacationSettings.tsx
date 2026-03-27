import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../UI/Buttons/Button';
import { Header } from '../UI/Typeography/Header';
import { DropdownList } from '../UI/DropdownList';
import { DateField } from '../UI/Fields/DateField';
import { UsersDropdown } from '../UI/form/UsersDropdown';
import { UserPerformer, EBgColorTypes } from '../UI/UserPerformer';
import { TUserListItem } from '../../types/user';
import { ETaskPerformerType } from '../../types/template';
import { TUsersDropdownOption } from '../UI/form/UsersDropdown';
import { formatDateLocal } from '../../utils/formatDateLocal';
import { useSubstituteUsers } from '../../utils/useSubstituteUsers';

import styles from './VacationSettings.css';

const NOOP = () => {};

export interface IVacationSettingsProps {
  isAbsent: boolean;
  absenceStatus?: string;
  vacationStartDate: string | null;
  vacationEndDate: string | null;
  substituteUserIds: number[];
  availableUsers: TUserListItem[];
  onActivate: (data: {
    substituteUserIds: number[];
    vacationStartDate: string | null;
    vacationEndDate: string | null;
    absenceStatus: string;
  }) => void;
  onDeactivate: () => void;
  isLoading: boolean;
}

export function VacationSettings({
  isAbsent,
  absenceStatus,
  vacationStartDate,
  vacationEndDate,
  substituteUserIds,
  availableUsers,
  onActivate,
  onDeactivate,
  isLoading,
}: IVacationSettingsProps) {
  const { formatMessage } = useIntl();

  const initStartDate = vacationStartDate || formatDateLocal(new Date());

  const [activeTab, setActiveTab] = useState<string>('active');
  const [startDate, setStartDate] = useState<string | null>(initStartDate);
  const [endDate, setEndDate] = useState<string | null>(vacationEndDate || null);
  const [hasSubmitted, setHasSubmitted] = useState<boolean>(false);
  const [dateError, setDateError] = useState<string | undefined>(undefined);

  const {
    selectedUserIds,
    mapUserOptions,
    selectedUserOptions,
    handleAddUser: rawHandleAddUser,
    handleRemoveUser,
  } = useSubstituteUsers(availableUsers, substituteUserIds || []);

  const handleAddUser = (selected: TUsersDropdownOption) => {
    rawHandleAddUser(selected);
    if (hasSubmitted) setHasSubmitted(false);
  };

  useEffect(() => {
    setActiveTab(isAbsent ? (absenceStatus || 'vacation') : 'active');
  }, [isAbsent, absenceStatus]);

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
    setStartDate(formatted);
    validateDates(formatted, endDate);
  };

  const handleEndDateChange = (date: Date | null) => {
    const formatted = formatDateLocal(date);
    setEndDate(formatted);
    validateDates(startDate, formatted);
  };

  const handleActivate = () => {
    setHasSubmitted(true);
    if (activeTab !== 'active' && selectedUserIds.length === 0) return;
    if (!validateDates(startDate, endDate)) return;

    onActivate({
      substituteUserIds: selectedUserIds,
      absenceStatus: activeTab,
      vacationStartDate: startDate || null,
      vacationEndDate: endDate || null,
    });
  };

  const STATUS_OPTIONS = [
    { value: 'active', label: formatMessage({ id: 'user-info.vacation.type.active', defaultMessage: 'Active' }) },
    { value: 'vacation', label: formatMessage({ id: 'user-info.vacation.type.vacation' }) },
    { value: 'sick_leave', label: formatMessage({ id: 'user-info.vacation.type.sick-leave' }) },
  ];

  return (
    <div className={styles['vacation-settings']} data-testid="vacation-settings">
      <Header size="6" tag="h2" className={styles['header']}>
        {formatMessage({ id: 'user-info.vacation.title' })}
      </Header>

      <div className={styles['vacation-form']} data-testid="vacation-form">
        <DropdownList
          label={formatMessage({ id: 'user-info.vacation.status', defaultMessage: 'Options' })}
          options={STATUS_OPTIONS}
          value={STATUS_OPTIONS.find(o => o.value === activeTab)}
          onChange={(option: { value: string }) => setActiveTab(option.value)}
          controlSize="lg"
          isSearchable={false}
          className={styles['status-dropdown']}
        />

        {activeTab !== 'active' && (
          <div className={styles['form-content']}>
            <div className={styles['dates-row']}>
              <div className={styles['date-field']} data-testid="vacation-start-input">
                <DateField
                  value={startDate || null}
                  onChange={handleStartDateChange}
                  fieldSize="lg"
                  title={formatMessage({ id: 'user-info.vacation.start-date' })}
                />
              </div>
              <div className={styles['date-field']} data-testid="vacation-end-input">
                <DateField
                  value={endDate || null}
                  onChange={handleEndDateChange}
                  fieldSize="lg"
                  title={formatMessage({ id: 'user-info.vacation.end-date' })}
                  errorMessage={dateError}
                />
              </div>
            </div>

            <div className={styles['vacation-substitutes']}>
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
                errorMessage={hasSubmitted && selectedUserIds.length === 0 ? formatMessage({ id: 'validation.required', defaultMessage: 'Please select at least one substitute.' }) : undefined}
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
          </div>
        )}

        {isAbsent && activeTab === 'active' && (
          <div className={styles['vacation-active']}>
            <p>{formatMessage({ id: 'user-info.vacation.active' })}</p>
          </div>
        )}

        <div className={styles['vacation-actions']}>
          {activeTab !== 'active' && (
            <Button
              label={formatMessage({ id: 'user-info.change-submit', defaultMessage: 'Save changes' })}
              onClick={handleActivate}
              isLoading={isLoading}
              disabled={isLoading}
              size="lg"
              buttonStyle="yellow"
              data-testid="vacation-activate-btn"
            />
          )}
          {activeTab === 'active' && isAbsent && (
            <Button
              label={formatMessage({ id: 'user-info.change-submit', defaultMessage: 'Save changes' })}
              onClick={onDeactivate}
              isLoading={isLoading}
              disabled={isLoading}
              size="lg"
              buttonStyle="yellow"
              data-testid="vacation-deactivate-btn"
            />
          )}
        </div>
      </div>
    </div>
  );
}
