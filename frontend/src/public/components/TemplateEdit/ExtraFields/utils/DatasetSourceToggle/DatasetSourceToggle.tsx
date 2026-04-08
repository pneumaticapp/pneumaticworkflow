import * as React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
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
import { useCheckDevice } from '../../../../../hooks/useCheckDevice';

import styles from './DatasetSourceToggle.css';

export function DatasetSourceToggle({ field, editField, isDisabled = false, children }: IDatasetSourceToggleProps) {
  const intl = useIntl();
  const { isMobile } = useCheckDevice();
  const dispatch = useDispatch();
  const datasetsList: IDatasetListItem[] = useSelector(getAllDatasetsList);
  const isLoading: boolean = useSelector(getIsAllDatasetsLoading);
  const isLoaded: boolean = useSelector(getIsAllDatasetsLoaded);

  const initialMode = field.dataset ? ESourceMode.Dataset : ESourceMode.Custom;
  const [currentMode, setCurrentMode] = useState<ESourceMode>(initialMode);
  
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  
  const [savedSelections, setSavedSelections] = useState<IExtraFieldSelection[] | null>(null);
  const [savedDataset, setSavedDataset] = useState<number | null>(null);

  const renderDatasetOption = useCallback((option: IDatasetOption) => {
    if (isMobile || !isMenuOpen) {
      return (
        <div className={styles['dataset-source-toggle__option-text']}>
          {option.label}
        </div>
      );
    }

    return (
      <TruncatedTooltip 
        label={option.label}
        containerClassName={styles['dataset-source-toggle__tooltip-container']}
        trigger="mouseenter"
        delay={[200, 0]}
      >
        <div className={styles['dataset-source-toggle__option-text']}>
          {option.label}
        </div>
      </TruncatedTooltip>
    );
  }, [isMobile, isMenuOpen]);

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
      setIsMenuOpen((prev) => !prev);
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
      setSavedSelections(field.selections as IExtraFieldSelection[] || null);
      editField({ 
        dataset: savedDataset,
        selections: undefined,
      });
      setIsMenuOpen(true);
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

  const clearButton = (
    <button
      type="button"
      className={styles['dataset-source-toggle__clear-btn']}
      onClick={handleClearDataset}
      disabled={!field.dataset}
    >
      {intl.formatMessage({ id: 'template.field-dataset-clear' })}
    </button>
  );

  const leftPanel = (
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
                {...(isMobile ? { trigger: 'click' } : {})}
              >
                <span className={classnames(styles['dataset-source-toggle__info-tag'], styles['dataset-source-toggle__option-text'])}>
                  {selectedDatasetOption?.label}
                </span>
              </TruncatedTooltip>
            )}
          </div>
          {!isDisabled && clearButton}
        </div>
      )}
    </div>
  );

  const rightPanel = (
    <OutsideClickHandler onOutsideClick={handleOutsideClick}>
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
      </div>
    </OutsideClickHandler>
  );

  return (
    <div className={styles['dataset-source-toggle']}>
      {leftPanel}
      {!isDisabled && rightPanel}
    </div>
  );
}
