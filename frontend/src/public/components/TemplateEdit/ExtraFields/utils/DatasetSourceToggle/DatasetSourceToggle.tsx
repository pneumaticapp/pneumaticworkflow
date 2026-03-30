import * as React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import OutsideClickHandler from 'react-outside-click-handler';

import { DropdownList } from '../../../../UI/DropdownList';
import { loadAllDatasets } from '../../../../../redux/datasets/slice';
import { getAllDatasetsList, getIsAllDatasetsLoading, getIsAllDatasetsLoaded } from '../../../../../redux/selectors/datasets';
import { IDatasetListItem } from '../../../../../types/dataset';
import { getEmptySelection } from '../../../KickoffRedux/utils/getEmptySelection';

import { ESourceMode, IDatasetOption, IDatasetSourceToggleProps } from './types';
import { IExtraFieldSelection } from '../../../../../types/template';
import { TruncatedTooltip } from './TruncatedTooltip';

import styles from './DatasetSourceToggle.css';

const renderDatasetOption = (option: IDatasetOption) => (
  <TruncatedTooltip 
    label={option.label}
    containerClassName={styles['dataset-source-toggle__tooltip-container']}
  >
    <div className={styles['dataset-source-toggle__option-text']}>
      {option.label}
    </div>
  </TruncatedTooltip>
);

export function DatasetSourceToggle({ field, editField, isDisabled = false, children }: IDatasetSourceToggleProps) {
  const intl = useIntl();
  const dispatch = useDispatch();
  const datasetsList: IDatasetListItem[] = useSelector(getAllDatasetsList);
  const isLoading: boolean = useSelector(getIsAllDatasetsLoading);
  const isLoaded: boolean = useSelector(getIsAllDatasetsLoaded);

  const initialMode = field.dataset ? ESourceMode.Dataset : ESourceMode.Custom;
  const [currentMode, setCurrentMode] = useState<ESourceMode>(initialMode);
  
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  
  const [savedSelections, setSavedSelections] = useState<IExtraFieldSelection[] | null>(null);
  const [savedDataset, setSavedDataset] = useState<number | null>(null);

  useEffect(() => {
    if (!isLoaded && !isLoading) {
      dispatch(loadAllDatasets());
    }
  }, [isLoaded, isLoading, dispatch]);

  const datasetOptions: IDatasetOption[] = useMemo(
    () => datasetsList.map((dataset) => ({
      label: dataset.name,
      value: String(dataset.id),
    })),
    [datasetsList],
  );

  const selectedDatasetOption = useMemo(
    () => datasetOptions.find((option) => option.value === String(field.dataset)) || null,
    [datasetOptions, field.dataset],
  );

  const handleToggle = (mode: ESourceMode) => {
    if (currentMode === mode && mode === ESourceMode.Dataset) {
      setIsMenuOpen(true);
      return;
    }
    
    setCurrentMode(mode);

    if (mode === ESourceMode.Custom) {
      setSavedDataset(field.dataset || null);
      editField({
        dataset: null,
        selections: savedSelections || [getEmptySelection()],
      });
      setIsMenuOpen(false); 
    } else {
      setSavedSelections(field.selections || null);
      
      if (savedDataset) {
        editField({ 
          dataset: savedDataset,
          selections: undefined,
        });
        setIsMenuOpen(false);
      } else {
        setIsMenuOpen(true);
      }
    }
  };

  const handleDatasetChange = (option: IDatasetOption) => {
    editField({ dataset: Number(option.value), selections: undefined });
    setIsMenuOpen(false);
  };

  const tabs = [
    { id: ESourceMode.Custom, label: intl.formatMessage({ id: 'template.field-source-custom' }) },
    { id: ESourceMode.Dataset, label: intl.formatMessage({ id: 'template.field-source-dataset' }) },
  ];

  const handleClearDataset = () => {
    editField({ dataset: null, selections: savedSelections || [getEmptySelection()] });
    setIsMenuOpen(true);
  };

  const handleOutsideClick = () => {
    setIsMenuOpen(false);
    if (currentMode === ESourceMode.Dataset && !field.dataset) {
      handleToggle(ESourceMode.Custom);
    }
  };

  return (
    <div className={styles['dataset-source-toggle']}>
      <div className={styles['dataset-source-toggle__left']}>
        {currentMode === ESourceMode.Custom && children}

        {currentMode === ESourceMode.Dataset && (
          <div className={styles['dataset-source-toggle__info']}>
            <div className={styles['dataset-source-toggle__info-dataset']}>
              <span className={styles['dataset-source-toggle__info-label']}>
                {intl.formatMessage({ id: 'template.datasets' })}:
              </span>
              {field.dataset && (
                <TruncatedTooltip 
                  label={selectedDatasetOption?.label}
                  containerClassName={styles['dataset-source-toggle__info-tag-tooltip']}
                >
                  <span className={classnames(styles['dataset-source-toggle__info-tag'], styles['dataset-source-toggle__option-text'])}>
                    {selectedDatasetOption?.label}
                  </span>
                </TruncatedTooltip>
              )}
            </div>
            <button
              type="button"
              className={styles['dataset-source-toggle__clear-btn']}
              onClick={handleClearDataset}
              disabled={isDisabled || !field.dataset}
            >
              {intl.formatMessage({ id: 'template.field-dataset-clear' })}
            </button>
          </div>
        )}
      </div>

      <div className={styles['dataset-source-toggle__right']}>
        <div className={styles['dataset-source-toggle__tabs']}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              disabled={isDisabled}
              onClick={() => handleToggle(tab.id as ESourceMode)}
              className={classnames(
                styles['dataset-source-toggle__tab'],
                currentMode === tab.id && styles['dataset-source-toggle__tab_active'],
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <OutsideClickHandler onOutsideClick={handleOutsideClick}>
          <div
            className={styles['dataset-source-toggle__dropdown-popup']}
            style={{ display: currentMode === ESourceMode.Dataset && isMenuOpen ? 'block' : 'none' }}
          >
            <DropdownList
              controlSize="sm"
              staticMenu
              options={datasetOptions}
              onChange={handleDatasetChange}
              value={selectedDatasetOption}
              placeholder={intl.formatMessage({ id: 'template.field-select-dataset' })}
              isDisabled={isDisabled}
              isSearchable={false}
              maxMenuHeight={240}
              formatOptionLabel={renderDatasetOption}
            />
          </div>
        </OutsideClickHandler>
      </div>
    </div>
  );
}
