import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../UI/Buttons/Button';
import { Header } from '../UI/Typeography/Header';
import { DropdownList } from '../UI/DropdownList';
import { DateField } from '../UI/Fields/DateField';
import { UsersDropdown, EOptionTypes } from '../UI/form/UsersDropdown';
import { UserPerformer, EBgColorTypes } from '../UI/UserPerformer';
import { TUserListItem } from '../../types/user';
import { ETaskPerformerType } from '../../types/template';
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
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>(substituteUserIds || []);
  const [hasSubmitted, setHasSubmitted] = useState<boolean>(false);

  useEffect(() => {
    setActiveTab(isAbsent ? (absenceStatus || 'vacation') : 'active');
  }, [isAbsent, absenceStatus]);

  const handleActivate = () => {
    setHasSubmitted(true);
    if (activeTab !== 'active' && selectedUserIds.length === 0) return;
    
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
        if (hasSubmitted) setHasSubmitted(false);
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
        <DropdownList
          label={formatMessage({ id: 'user-info.vacation.status', defaultMessage: 'Options' })}
          options={STATUS_OPTIONS}
          value={STATUS_OPTIONS.find(o => o.value === activeTab)}
          onChange={(option: any) => setActiveTab(option.value)}
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
                  onChange={(date: Date | null) => setStartDate(formatDateLocal(date))}
                  fieldSize="lg"
                  title={formatMessage({ id: 'user-info.vacation.start-date' })}
                />
              </div>
              <div className={styles['date-field']} data-testid="vacation-end-input">
                <DateField
                  value={endDate || null}
                  onChange={(date: Date | null) => setEndDate(formatDateLocal(date))}
                  fieldSize="lg"
                  title={formatMessage({ id: 'user-info.vacation.end-date' })}
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
                onClickInvite={() => {}}
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
