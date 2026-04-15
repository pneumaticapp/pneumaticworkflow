import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { TemplatesSortingContainer } from './TemplatesSortingContainer';
import { TopNavContainer } from '../../components/TopNav';
import { SelectMenu, Tabs } from '../../components/UI';
import { ERoutes } from '../../constants/routes';
import { datasetsSortingValues } from '../../constants/sortings';
import { setDatasetsListSorting } from '../../redux/datasets/slice';
import { getDatasetsSorting } from '../../redux/selectors/datasets';
import { EDatasetsSorting } from '../../types/dataset';
import { ETemplatesTab, ITemplatesLayoutProps } from '../../types/template';
import { history } from '../../utils/history';

import styles from './TemplatesLayout.css';

import { ReturnLink } from '../../components/UI/ReturnLink';

export function TemplatesLayout({ children }: ITemplatesLayoutProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();


  const datasetsSorting = useSelector(getDatasetsSorting);

  const handleDatasetsSortingChange = (value: EDatasetsSorting) => {
    dispatch(setDatasetsListSorting(value));
  };

  const isDatasetDetail = /^\/datasets\/\d+\/?$/.test(history.location.pathname);

  const activeTab = history.location.pathname.startsWith(ERoutes.Datasets)
    ? ETemplatesTab.Datasets
    : ETemplatesTab.Templates;

  const tabValues = [
    {
      id: ETemplatesTab.Templates,
      label: formatMessage({ id: 'templates.tab-templates' }),
    },
    {
      id: ETemplatesTab.Datasets,
      label: formatMessage({ id: 'templates.tab-datasets' }),
    },
  ];

  const handleTabChange = (tabId: ETemplatesTab) => {
    if (tabId === ETemplatesTab.Datasets) {
      history.push(ERoutes.Datasets);
    } else {
      history.push(ERoutes.Templates);
    }
  };

  const renderLeftContent = () => {
    if (isDatasetDetail) {
      return (
        <div className={styles['navbar-left__content']}>
          <ReturnLink
            className={styles['return-link']}
            label={formatMessage({ id: 'datasets.all-datasets' })}
            route={ERoutes.Datasets}
          />
        </div>
      );
    }

    return (
      <div className={styles['navbar-left__content']}>
          <Tabs
            activeValueId={activeTab}
            values={tabValues}
            onChange={handleTabChange}
          />
          {activeTab === ETemplatesTab.Templates && <TemplatesSortingContainer />}
          {activeTab === ETemplatesTab.Datasets && (
            <SelectMenu
              closeOnSelect
              activeValue={datasetsSorting}
              values={datasetsSortingValues}
              toggleTextClassName={styles['dataset__sorting-toggle-text']}
              onChange={handleDatasetsSortingChange}
            />
          )}
      </div>
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main>
        <div className="container-fluid">
          {children}
        </div>
      </main>
    </>
  );
}
