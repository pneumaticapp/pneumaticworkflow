import * as React from 'react';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import InfiniteScroll from 'react-infinite-scroll-component';
import { IDatasetListItem } from '../../types/dataset';

import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../constants/defaultValues';
import { openCreateModal, loadDatasets } from '../../redux/datasets/slice';
import { getDatasetsListSelection, getDatasetsIsLoading } from '../../redux/selectors/datasets';
import { AddCardButton } from '../UI';
import { AIPlusIcon } from '../icons';
import { DatasetModal } from './DatasetModal/DatasetModal';
import { EDatasetModalType } from './DatasetModal/types';
import { DatasetCard } from './DatasetCard';

import styles from './Datasets.css';

export function Datasets() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { items: datasetsList, count, offset } = useSelector(getDatasetsListSelection) || { items: [], count: 0, offset: 0 };
  const isLoading = useSelector(getDatasetsIsLoading);

  useEffect(() => {
    dispatch(loadDatasets(0));
  }, [dispatch]);

  const handleOpenCreateModal = () => {
    dispatch(openCreateModal());
  };

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.Datasets} withUnderline={false} />
      <InfiniteScroll
        dataLength={datasetsList.length}
        next={() => dispatch(loadDatasets(offset + 1))}
        loader={null}
        hasMore={count > datasetsList.length || isLoading}
        className={classnames(styles['cards-wrapper'], { [styles['container-loading']]: isLoading })}
        scrollableTarget="app-container"
      >
        {isLoading && datasetsList.length === 0 && <div className="loading" />}
        <AddCardButton
          className={styles['card']}
          onClick={handleOpenCreateModal}
          title={formatMessage({ id: 'datasets.new-dataset.title' })}
          caption={formatMessage({ id: 'datasets.new-dataset.caption' })}
          icon={<AIPlusIcon />}
        />
        {datasetsList.map((dataset: IDatasetListItem) => (
          <DatasetCard key={dataset.id} {...dataset} />
        ))}
      </InfiniteScroll>
      <DatasetModal type={EDatasetModalType.Create} />
      <DatasetModal type={EDatasetModalType.Edit} />
    </div>
  );
}

export default Datasets;
