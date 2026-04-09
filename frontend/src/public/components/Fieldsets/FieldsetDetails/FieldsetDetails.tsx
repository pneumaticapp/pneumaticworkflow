import * as React from 'react';
import { useEffect, useState, useMemo, useCallback } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  deleteFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
  updateFieldsetAction,
} from '../../../redux/fieldsets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';

import { EExtraFieldType, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor, EMoveDirections } from '../../../types/workflow';
import { ExtraFieldsMap } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../../TemplateEdit/ExtraFields';
import { getEmptyField } from '../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';

import {
  mapFieldsetFieldsToExtraFields,
  mapExtraFieldsToFieldsetFields,
} from './fieldsetFieldMappers';

import { TFieldsetDetailsProps } from './types';
import styles from './FieldsetDetails.css';

const FieldsetDetails = ({ match: { params: { id: matchParamId } } }: TFieldsetDetailsProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const fieldset = useSelector(getCurrentFieldset);
  const isLoading = useSelector(isCurrentFieldsetLoading);
  const accountId = useSelector(getAccountId);

  const [localFields, setLocalFields] = useState<IExtraField[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    const id = Number(matchParamId);
    if (Number.isNaN(id)) {
      history.push(ERoutes.Fieldsets);

      return;
    }
    if (fieldset?.id === id) return;

    dispatch(loadCurrentFieldset({ id }));
  }, [matchParamId]);

  useEffect(() => {
    return () => {
      dispatch(resetCurrentFieldset());
    };
  }, []);

  // Sync local fields when fieldset loads/updates from server
  useEffect(() => {
    if (fieldset?.fields) {
      setLocalFields(mapFieldsetFieldsToExtraFields(fieldset.fields));
      setHasUnsavedChanges(false);
    }
  }, [fieldset?.fields]);

  const getSortedFields = useCallback(() => {
    return [...localFields].sort((a, b) => b.order - a.order);
  }, [localFields]);

  const sortedFields = useMemo(() => getSortedFields(), [getSortedFields]);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = getNormalizeFieldsOrders([...localFields, getEmptyField(type, formatMessage)]);
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleDeleteField = (idx: number) => {
    const newFields = getSortedFields().filter((_, index) => index !== idx);
    setLocalFields(getNormalizeFieldsOrders(newFields));
    setHasUnsavedChanges(true);
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const newFields = moveWorkflowField(from, to, getSortedFields());
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleSaveFields = () => {
    if (!fieldset) return;
    dispatch(updateFieldsetAction({
      id: fieldset.id,
      fields: mapExtraFieldsToFieldsetFields(localFields),
    }));
    setHasUnsavedChanges(false);
  };

  if (isLoading || !fieldset) {
    return <FieldsetDetailsSkeleton />;
  }

  return (
    <div className={styles['container']}>
      <header className={styles['header']}>
        <h1 title={fieldset.name}>{fieldset.name}</h1>
        <div className={styles['header__config']}>
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onDelete={() => {
              dispatch(deleteFieldsetAction({ id: fieldset.id }));
              history.push(ERoutes.Fieldsets);
            }}
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>

      {fieldset.description && (
        <p className={styles['description']}>{fieldset.description}</p>
      )}

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.fields-section' })}
        </h2>

        <div className={styles['components']}>
          {ExtraFieldsMap.map((x) => (
            <ExtraFieldIcon {...x} key={x.id} onClick={() => handleCreateField(x.id)} />
          ))}
        </div>

        {sortedFields.length > 0 && (
          <div className={styles['fields']}>
            {sortedFields.map((field, index) => (
              <ExtraFieldIntl
                key={field.apiName}
                id={index}
                field={field}
                fieldsCount={sortedFields.length}
                labelBackgroundColor={EInputNameBackgroundColor.White}
                deleteField={() => handleDeleteField(index)}
                moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
                moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
                editField={handleEditField(field.apiName)}
                accountId={accountId}
              />
            ))}
          </div>
        )}

        {sortedFields.length === 0 && (
          <p className={styles['empty-text']}>
            {formatMessage({ id: 'fieldsets.no-fields' })}
          </p>
        )}

        {hasUnsavedChanges && (
          <div className={styles['save-bar']}>
            <Button
              label={formatMessage({ id: 'fieldsets.save-fields' })}
              buttonStyle="yellow"
              size="md"
              onClick={handleSaveFields}
            />
            <span className={styles['save-bar__hint']}>
              {formatMessage({ id: 'fieldsets.unsaved-changes' })}
            </span>
          </div>
        )}
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.rules-section' })}
        </h2>
        {fieldset.rules.length === 0 ? (
          <p className={styles['empty-text']}>
            {formatMessage({ id: 'fieldsets.no-rules' })}
          </p>
        ) : (
          <table className={styles['fields-table']}>
            <thead>
              <tr>
                <th>Type</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {fieldset.rules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.type}</td>
                  <td>{rule.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
};

export default FieldsetDetails;
