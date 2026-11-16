import * as React from 'react';
import { useState } from 'react';

import { SelectManagerModal } from '../SelectManagerModal';
import { SelectReportsModal } from '../SelectReportsModal';
import type { ITeamUserRelationsModalsProps } from './types';

export function TeamUserRelationsModals({
  user,
  isManagerModalOpen,
  isReportsModalOpen,
  onCloseManagerModal,
  onCloseReportsModal,
  handleChangeUserManager,
  handleChangeUserReports,
}: ITeamUserRelationsModalsProps) {
  const [isManagerSaving, setIsManagerSaving] = useState(false);
  const [isReportsSaving, setIsReportsSaving] = useState(false);

  const handleCloseManagerModal = () => {
    if (!isManagerSaving) onCloseManagerModal();
  };

  const handleConfirmManager = (managerId: number | null) => {
    setIsManagerSaving(true);
    handleChangeUserManager(user.id, managerId, {
      onSuccess: () => {
        setIsManagerSaving(false);
        onCloseManagerModal();
      },
      onError: () => setIsManagerSaving(false),
    });
  };

  const handleCloseReportsModal = () => {
    if (!isReportsSaving) onCloseReportsModal();
  };

  const handleConfirmReports = (reportIds: number[]) => {
    setIsReportsSaving(true);
    handleChangeUserReports(user.id, reportIds, {
      onSuccess: () => {
        setIsReportsSaving(false);
        onCloseReportsModal();
      },
      onError: () => setIsReportsSaving(false),
    });
  };

  return (
    <>
      {isManagerModalOpen && (
        <SelectManagerModal
          isOpen={isManagerModalOpen}
          onClose={handleCloseManagerModal}
          onConfirm={handleConfirmManager}
          currentUserId={user.id}
          currentManagerId={user.managerId || null}
          isLoading={isManagerSaving}
        />
      )}
      {isReportsModalOpen && (
        <SelectReportsModal
          isOpen={isReportsModalOpen}
          onClose={handleCloseReportsModal}
          onConfirm={handleConfirmReports}
          currentUserId={user.id}
          currentReportIds={user.reportIds || []}
          isLoading={isReportsSaving}
        />
      )}
    </>
  );
}
