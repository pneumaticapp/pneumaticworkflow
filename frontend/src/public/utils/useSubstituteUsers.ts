import { useState, useCallback, useEffect } from 'react';
import { TUserListItem } from '../types/user';
import { getUserFullName } from './users';
import { EOptionTypes, TUsersDropdownOption } from '../components/UI/form/UsersDropdown';

export interface ISubstituteUsersResult {
  selectedUserIds: number[];
  setSelectedUserIds: React.Dispatch<React.SetStateAction<number[]>>;
  mapUserOptions: TUsersDropdownOption[];
  selectedUserOptions: TUsersDropdownOption[];
  handleAddUser: (selected: TUsersDropdownOption) => void;
  handleRemoveUser: (selected: TUsersDropdownOption) => void;
}

/**
 * Shared hook for managing substitute user selection.
 * Used in both VacationSettings (Team page) and ProfileVacationFields (Profile page).
 */
export function useSubstituteUsers(
  availableUsers: TUserListItem[],
  initialIds: number[],
  onChangeCallback?: (nextIds: number[]) => void,
): ISubstituteUsersResult {
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>(initialIds);

  useEffect(() => {
    setSelectedUserIds(initialIds);
  }, [initialIds]);

  const mapUserOptions: TUsersDropdownOption[] = availableUsers.map((u) => ({
    ...u,
    optionType: EOptionTypes.User,
    value: String(u.id),
    label: getUserFullName({ firstName: u.firstName, lastName: u.lastName }),
  })) as TUsersDropdownOption[];

  const handleAddUser = useCallback(
    (selected: TUsersDropdownOption) => {
      if (selected && selected.id) {
        const id = Number(selected.id);
        setSelectedUserIds((prev) => {
          if (prev.includes(id)) return prev;
          const next = [...prev, id];
          onChangeCallback?.(next);
          return next;
        });
      }
    },
    [onChangeCallback],
  );

  const handleRemoveUser = useCallback(
    (selected: TUsersDropdownOption) => {
      if (selected && selected.id) {
        const id = Number(selected.id);
        setSelectedUserIds((prev) => {
          const next = prev.filter((userId) => userId !== id);
          onChangeCallback?.(next);
          return next;
        });
      }
    },
    [onChangeCallback],
  );

  const selectedUserOptions = mapUserOptions.filter((opt) => selectedUserIds.includes(opt.id));

  return {
    selectedUserIds,
    setSelectedUserIds,
    mapUserOptions,
    selectedUserOptions,
    handleAddUser,
    handleRemoveUser,
  };
}
