import * as React from 'react';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';

import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../constants/defaultValues';
import { openCreateModal } from '../../redux/datasets/slice';
import { AddCardButton } from '../UI';
import { RoundDocIcon } from '../icons';

import styles from '../Templates/Templates.css';

export function Datasets() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const handleOpenCreateModal = () => {
    dispatch(openCreateModal());
  };

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.Datasets} withUnderline={false} />
      <div className={styles['cards-wrapper']}>
        <AddCardButton
          className={styles['card']}
          onClick={handleOpenCreateModal}
          title={formatMessage({ id: 'datasets.new-dataset.title' })}
          caption={formatMessage({ id: 'datasets.new-dataset.caption' })}
          icon={<RoundDocIcon />}
        />
      </div>
    </div>
  );
}

export default Datasets;
