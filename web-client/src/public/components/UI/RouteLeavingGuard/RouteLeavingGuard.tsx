import { Location } from 'history';
import React, { useEffect, useState } from 'react';
import { Prompt } from 'react-router-dom';

import { Header, Modal } from '..';

import styles from './RouteLeavingGuard.css';

interface Props {
  when?: boolean;
  title: string;
  message: string;
  onConfirm: (path: string) => void;
  onReject: (path: string) => void;
  shouldBlockNavigation: (location: Location) => boolean;
  renderControlls(confirm: () => void, reject: () => void): React.ReactNode;
}

type TGaurdState = 'confirmed' | 'rejected' | 'none';

export function RouteLeavingGuard({
  when,
  title,
  message,
  onConfirm,
  onReject,
  shouldBlockNavigation,
  renderControlls,
}: Props) {
  const [modalVisible, setModalVisible] = useState(false);
  const [lastLocation, setLastLocation] = useState<Location | null>(null);
  const [confirmedNavigation, setConfirmedNavigation] = useState<TGaurdState>('none');

  const closeModal = () => {
    setModalVisible(false);
  };

  const handleBlockedNavigation = (nextLocation: Location): boolean => {
    if (shouldBlockNavigation(nextLocation) && confirmedNavigation === 'none') {
      setModalVisible(true);
      setLastLocation(nextLocation);
      return false;
    }
    return true;
  };

  const handleConfirm = () => {
    setModalVisible(false);
    setConfirmedNavigation('confirmed');
  };

  const handleReject = () => {
    setModalVisible(false);
    setConfirmedNavigation('rejected');
  }

  useEffect(() => {
    if (!lastLocation) {
      return;
    }

    const actionMap = {
      confirmed: () => onConfirm(lastLocation.pathname),
      rejected: () => onReject(lastLocation.pathname),
      none: () => { },
    }

    actionMap[confirmedNavigation]();
    setConfirmedNavigation('none');
  }, [confirmedNavigation, lastLocation]);

  return (
    <>
      <Prompt when={when} message={handleBlockedNavigation} />

      <Modal
        isOpen={modalVisible}
        onClose={closeModal}
      >
        <Header tag="p" size="6">
          {title}
        </Header>

        <p className={styles['message']}>{message}</p>

        <div className={styles['controlls']}>
          {renderControlls(handleConfirm, handleReject)}
        </div>
      </Modal>
    </>
  );
};
