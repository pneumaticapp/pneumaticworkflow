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

  return (
    <>
      {isManagerModalOpen && (
        <SelectManagerModal
          isOpen={isManagerModalOpen}
          onClose={() => {
            if (!isManagerSaving) {
              onCloseManagerModal();
            }
          }}
          onConfirm={(managerId) => {
            setIsManagerSaving(true);
            handleChangeUserManager(user.id, managerId, {
              onSuccess: () => {
                setIsManagerSaving(false);
                onCloseManagerModal();
              },
              onError: () => {
                setIsManagerSaving(false);
              },
            });
          }}
          currentUserId={user.id}
          currentManagerId={user.managerId || null}
          isLoading={isManagerSaving}
        />
      )}
      {isReportsModalOpen && (
        <SelectReportsModal
          isOpen={isReportsModalOpen}
          onClose={() => {
            if (!isReportsSaving) {
              onCloseReportsModal();
            }
          }}
          onConfirm={(reportIds) => {
            setIsReportsSaving(true);
            handleChangeUserReports(user.id, reportIds, {
              onSuccess: () => {
                setIsReportsSaving(false);
                onCloseReportsModal();
              },
              onError: () => {
                setIsReportsSaving(false);
              },
            });
          }}
          currentUserId={user.id}
          currentReportIds={user.reportIds || []}
          isLoading={isReportsSaving}
        />
      )}
    </>
  );
}
