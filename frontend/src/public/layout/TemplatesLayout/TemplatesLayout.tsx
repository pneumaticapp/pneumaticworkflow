import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { TemplatesSortingContainer } from './TemplatesSortingContainer';
import { TopNavContainer } from '../../components/TopNav';
import { SelectMenu, Tabs } from '../../components/UI';
import { ERoutes } from '../../constants/routes';
import { datasetsSortingValues, fieldsetsSortingValues } from '../../constants/sortings';
import { setDatasetsListSorting } from '../../redux/datasets/slice';
import { setFieldsetsListSorting } from '../../redux/fieldsets/slice';
import { getDatasetsSorting } from '../../redux/selectors/datasets';
import { getFieldsetsSorting } from '../../redux/selectors/fieldsets';
import { EDatasetsSorting } from '../../types/dataset';
import { EFieldsetsSorting } from '../../types/fieldset';
import { ETemplatesTab, ITemplatesLayoutProps } from '../../types/template';
import { history } from '../../utils/history';

import styles from './TemplatesLayout.css';

import { ReturnLink } from '../../components/UI/ReturnLink';

export function TemplatesLayout({ children }: ITemplatesLayoutProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const datasetsSorting = useSelector(getDatasetsSorting);
  const fieldsetsSorting = useSelector(getFieldsetsSorting);

  const handleDatasetsSortingChange = (value: EDatasetsSorting) => {
    dispatch(setDatasetsListSorting(value));
  };

  const handleFieldsetsSortingChange = (value: EFieldsetsSorting) => {
    dispatch(setFieldsetsListSorting(value));
  };

  const isDatasetDetail = /^\/datasets\/\d+\/?$/.test(history.location.pathname);
  const isFieldsetDetail = /^\/fieldsets\/\d+\/?$/.test(history.location.pathname);

  const activeTab = history.location.pathname.startsWith(ERoutes.Fieldsets)
    ? ETemplatesTab.Fieldsets
    : history.location.pathname.startsWith(ERoutes.Datasets)
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
    {
      id: ETemplatesTab.Fieldsets,
      label: formatMessage({ id: 'templates.tab-fieldsets' }),
    },
  ];

  const handleTabChange = (tabId: ETemplatesTab) => {
    if (tabId === ETemplatesTab.Datasets) {
      history.push(ERoutes.Datasets);
    } else if (tabId === ETemplatesTab.Fieldsets) {
      history.push(ERoutes.Fieldsets);
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

    if (isFieldsetDetail) {
      return (
        <div className={styles['navbar-left__content']}>
          <ReturnLink
            className={styles['return-link']}
            label={formatMessage({ id: 'fieldsets.all-fieldsets' })}
            route={ERoutes.Fieldsets}
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
          {activeTab === ETemplatesTab.Fieldsets && (
            <SelectMenu
              activeValue={fieldsetsSorting}
              values={fieldsetsSortingValues}
              toggleTextClassName={styles['dataset__sorting-toggle-text']}
              onChange={handleFieldsetsSortingChange}
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
