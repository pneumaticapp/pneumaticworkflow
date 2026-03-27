import React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  cloneDatasetAction,
  deleteDatasetAction,
} from '../../../redux/datasets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button } from '../../UI';
import { BoldPlusIcon } from '../../icons';
import { DatasetModal } from '../DatasetModal/DatasetModal';
import { EDatasetModalType } from '../DatasetModal/types';

import { getCurrentDataset } from '../../../redux/selectors/datasets';

import styles from './DatasetDetails.css';

const DatasetDetails = () => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const dataset = useSelector(getCurrentDataset);

  if (!dataset) {
    return null;
  }

  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <h1 title={dataset.name}>{dataset.name}</h1>
        <div className={styles['header__config']}>
          <Button
            size="sm"
            icon={BoldPlusIcon}
            label={formatMessage({ id: 'datasets.add-row' })}
            buttonStyle="transparent-black"
            onClick={() => {}}
          />
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onClone={() => {
              dispatch(cloneDatasetAction({ id: dataset.id }));
              history.push(ERoutes.Datasets);
            }}
            onDelete={() => {
              dispatch(deleteDatasetAction({ id: dataset.id }));
              history.push(ERoutes.Datasets);
            }}
            editLabel={formatMessage({ id: 'datasets.edit' })}
            cloneLabel={formatMessage({ id: 'datasets.clone' })}
            deleteLabel={formatMessage({ id: 'datasets.delete' })}
          />
        </div>
      </header>
      <DatasetModal type={EDatasetModalType.Edit} />
    </div>
  );
};

export default DatasetDetails;
