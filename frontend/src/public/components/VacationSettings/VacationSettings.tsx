import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../UI/Buttons/Button';
import { Header } from '../UI/Typeography/Header';
import { Tabs } from '../UI/Tabs';
import { DateField } from '../UI/Fields/DateField';
import { UsersDropdown, EOptionTypes } from '../UI/form/UsersDropdown';
import { TUserListItem } from '../../types/user';
import { getUserFullName } from '../../utils/users';

import styles from './VacationSettings.css';

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

const formatDateLocal = (date: Date | null): string | null => {
  if (!date) return null;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

export function VacationSettings({
  isAbsent,
  absenceStatus,
  vacationStartDate,
  vacationEndDate,
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
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);

  useEffect(() => {
    setActiveTab(isAbsent ? (absenceStatus || 'vacation') : 'active');
  }, [isAbsent, absenceStatus]);

  const handleActivate = () => {
    onActivate({
      substituteUserIds: selectedUserIds,
      absenceStatus: activeTab,
      vacationStartDate: startDate || null,
      vacationEndDate: endDate || null,
    });
  };

  const STATUS_OPTIONS = [
    { id: 'active', label: formatMessage({ id: 'user-info.vacation.type.active', defaultMessage: 'Active' }) },
    { id: 'vacation', label: formatMessage({ id: 'user-info.vacation.type.vacation' }) },
    { id: 'sick_leave', label: formatMessage({ id: 'user-info.vacation.type.sick-leave' }) },
  ];

  const mapUserOptions = availableUsers.map(u => ({
    ...u,
    optionType: EOptionTypes.User,
    value: String(u.id),
    label: getUserFullName({ firstName: u.firstName, lastName: u.lastName }),
  }));

  const handleAddUser = (selected: any) => {
    if (selected && selected.id) {
      const id = Number(selected.id);
      if (!selectedUserIds.includes(id)) {
        setSelectedUserIds([...selectedUserIds, id]);
      }
    }
  };

  const handleRemoveUser = (selected: any) => {
    if (selected && selected.id) {
      const id = Number(selected.id);
      setSelectedUserIds((prev) => prev.filter(userId => userId !== id));
    }
  };

  const selectedUserOptions = mapUserOptions.filter(opt => selectedUserIds.includes(opt.id));

  return (
    <div className={styles['vacation-settings']} data-testid="vacation-settings">
      <Header size="6" tag="h2" className={styles['header']}>
        {formatMessage({ id: 'user-info.vacation.title' })}
      </Header>

      <div className={styles['vacation-form']} data-testid="vacation-form">
        <Tabs
          activeValueId={activeTab}
          values={STATUS_OPTIONS}
          onChange={(val) => setActiveTab(val as string)}
          containerClassName={styles['tabs-container']}
        />

        {activeTab !== 'active' && (
          <div className={styles['form-content']}>
            <div className={styles['vacation-dates']}>
              <div className={styles['vacation-field']} data-testid="vacation-start-input">
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label className={styles['vacation-field-label']}>
                  {formatMessage({ id: 'user-info.vacation.start-date' })}
                </label>
                <DateField
                  value={startDate || null}
                  onChange={(date: Date | null) => setStartDate(formatDateLocal(date))}
                  fieldSize="lg"
                  containerClassName={styles['date-field']}
                />
              </div>
              <div className={styles['vacation-field']} data-testid="vacation-end-input">
                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                <label className={styles['vacation-field-label']}>
                  {formatMessage({ id: 'user-info.vacation.end-date' })}
                </label>
                <DateField
                  value={endDate || null}
                  onChange={(date: Date | null) => setEndDate(formatDateLocal(date))}
                  fieldSize="lg"
                  containerClassName={styles['date-field']}
                />
              </div>
            </div>

            <div className={styles['vacation-substitutes']}>
              {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
              <label className={styles['vacation-field-label']}>
                {formatMessage({ id: 'user-info.vacation.substitutes' })}
              </label>
              <UsersDropdown
                isMulti
                controlSize="lg"
                options={mapUserOptions}
                value={selectedUserOptions}
                onChange={handleAddUser}
                onChangeSelected={handleRemoveUser}
                isSearchable
                placeholder={formatMessage({ id: 'user-info.vacation.substitutes' })}
                inviteLabel=""
                onClickInvite={() => {}}
              />
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
              label={formatMessage({ id: 'user-info.vacation.activate' })}
              onClick={handleActivate}
              isLoading={isLoading}
              size="sm"
              buttonStyle="yellow"
              data-testid="vacation-activate-btn"
            />
          )}
          {activeTab === 'active' && isAbsent && (
            <Button
              label={formatMessage({ id: 'user-info.vacation.deactivate' })}
              onClick={onDeactivate}
              isLoading={isLoading}
              size="sm"
              buttonStyle="transparent-black"
              data-testid="vacation-deactivate-btn"
            />
          )}
        </div>
      </div>
    </div>
  );
}
