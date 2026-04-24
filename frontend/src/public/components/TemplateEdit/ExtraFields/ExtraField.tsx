import * as React from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import classnames from 'classnames';
import { injectIntl} from 'react-intl';

import { ExtraFieldString } from './String';
import { ExtraFieldText } from './Text';
import { ExtraFieldUrl } from './Url';
import { ExtraFieldDate } from './Date';
import { ExtraFieldCheckbox } from './Checkbox';
import { ExtraFieldRadio } from './Radio';
import { ExtraFieldCreatable } from './Creatable';
import { ExtraFieldFile } from './File';
import { ExtraFieldUser } from './User';
import { ExtraFieldNumber } from './Number';

import { EExtraFieldType } from '../../../types/template';
import { ExtraFieldDropdown } from './utils/ExtraFieldDropdown';
import { getInputNameBackground } from './utils/getInputNameBackground';
import { getAllDatasetsList, getIsAllDatasetsLoading, getIsAllDatasetsLoaded } from '../../../redux/selectors/datasets';
import { loadAllDatasets } from '../../../redux/datasets/slice';
import { IExtraFieldProps } from './types';

import styles from '../KickoffRedux/KickoffRedux.css';

const DATASET_FIELD_TYPES = [EExtraFieldType.Checkbox, EExtraFieldType.Radio, EExtraFieldType.Creatable];

function ExtraField(props: IExtraFieldProps) {
  const {
    field,
    field: { apiName, isRequired = false, isHidden = false },
    fieldsCount,
    showDropdown = true,
    deleteField,
    moveFieldUp,
    moveFieldDown,
    editField,
    isDisabled = false,
    id,
    wrapperClassName,
    labelBackgroundColor,
    innerRef,
  } = props;

  const dispatch = useDispatch();

  const isDatasetField = DATASET_FIELD_TYPES.includes(field.type);

  const datasetsList = useSelector(getAllDatasetsList);
  const isDatasetsLoading = useSelector(getIsAllDatasetsLoading);
  const isDatasetsLoaded = useSelector(getIsAllDatasetsLoaded);

  useEffect(() => {
    if (isDatasetField && !isDatasetsLoaded && !isDatasetsLoading) {
      dispatch(loadAllDatasets());
    }
  }, [isDatasetField, isDatasetsLoaded, isDatasetsLoading, dispatch]);

  const datasetOptions = useMemo(
    () => datasetsList.map((dataset) => ({ label: dataset.name, value: String(dataset.id) })),
    [datasetsList],
  );

  const datasetName = useMemo(
    () => datasetOptions.find((option) => option.value === String(field.dataset))?.label,
    [datasetOptions, field.dataset],
  );

  const handleDatasetSelect = useCallback(
    (datasetId: number) => {
      editField({ dataset: datasetId, selections: undefined });
    },
    [editField],
  );

  const handleDeleteField = useCallback(() => {
    if (!deleteField) {
      return;
    }

    deleteField();
  }, [deleteField]);

  const handleMoveFieldUp = () => {
    if (!moveFieldUp) {
      return;
    }

    moveFieldUp();
  };

  const handleMoveFieldDown = () => {
    if (!moveFieldDown) {
      return;
    }

    moveFieldDown();
  };

  const renderField = () => {
    const fieldsMap: { [key in EExtraFieldType]: Function } = {
      [EExtraFieldType.Number]: ExtraFieldNumber,
      [EExtraFieldType.Text]: ExtraFieldText,
      [EExtraFieldType.String]: ExtraFieldString,
      [EExtraFieldType.Url]: ExtraFieldUrl,
      [EExtraFieldType.Date]: ExtraFieldDate,
      [EExtraFieldType.Checkbox]: ExtraFieldCheckbox,
      [EExtraFieldType.Radio]: ExtraFieldRadio,
      [EExtraFieldType.Creatable]: ExtraFieldCreatable,
      [EExtraFieldType.File]: ExtraFieldFile,
      [EExtraFieldType.User]: ExtraFieldUser,
    };

    const Field = fieldsMap[field.type];

    return <Field {...props} innerRef={innerRef} {...(isDatasetField && { datasetName })} />;
  };

  const isFirstItem = useMemo(() => id === 0 && id !== undefined, [id]);
  const isLastItem = useMemo(() => fieldsCount !== undefined && id === fieldsCount - 1, [id, fieldsCount]);

  const getFieldClassName = () => {
    const labelClassNameMap: { [key in EExtraFieldType]: string } = {
      [EExtraFieldType.Number]: 'with-label',
      [EExtraFieldType.Text]: 'with-label',
      [EExtraFieldType.String]: 'with-label',
      [EExtraFieldType.Url]: 'with-label',
      [EExtraFieldType.Date]: 'with-label',
      [EExtraFieldType.Checkbox]: 'without-label',
      [EExtraFieldType.Radio]: 'without-label',
      [EExtraFieldType.Creatable]: 'with-label',
      [EExtraFieldType.File]: 'without-label',
      [EExtraFieldType.User]: 'with-label',
    };

    const labelClassName = labelClassNameMap[field.type];

    return classnames(
      getInputNameBackground(labelBackgroundColor),
      wrapperClassName,
      styles[labelClassName],
      styles['kick-off-input'],
      showDropdown && !isDisabled && styles['kick-off-input_with-dropdown'],
    );
  };

  const getIsRequiredDisabled = () => {
    const isRequiredDisabledMap: { [key in EExtraFieldType]: boolean } = {
      [EExtraFieldType.Number]: false,
      [EExtraFieldType.Text]: false,
      [EExtraFieldType.String]: false,
      [EExtraFieldType.Url]: false,
      [EExtraFieldType.Date]: false,
      [EExtraFieldType.Checkbox]: false,
      [EExtraFieldType.Radio]: false,
      [EExtraFieldType.Creatable]: false,
      [EExtraFieldType.File]: false,
      [EExtraFieldType.User]: true,
    };

    return isRequiredDisabledMap[field.type];
  };

  const getDropdownClassName = () => {
    return classnames(
      styles['kick-off-input__dropdown'],
      (field.type === EExtraFieldType.Checkbox || field.type === EExtraFieldType.Radio) && styles['kick-off-input__dropdown_choices'],
      field.type === EExtraFieldType.Creatable && styles['kick-off-input__dropdown_creatable']
    );
  };

  return (
    <div className={getFieldClassName()}>
      {renderField()}

      {showDropdown && !isDisabled && (
        <div className={getDropdownClassName()}>
          <ExtraFieldDropdown
            isFirstItem={isFirstItem}
            isLastItem={isLastItem}
            apiName={apiName}
            isRequired={isRequired}
            isRequiredDisabled={getIsRequiredDisabled()}
            isHidden={isHidden}
            onEditField={editField}
            onMoveFieldUp={handleMoveFieldUp}
            onMoveFieldDown={handleMoveFieldDown}
            onDeleteField={handleDeleteField}
            showDatasetOption={isDatasetField}
            datasetOptions={datasetOptions}
            {...(field.dataset && { selectedDatasetId: field.dataset })}
            onDatasetSelect={handleDatasetSelect}
          />
        </div>
      )}
    </div>
  );
}

export const ExtraFieldIntl = injectIntl(ExtraField);
