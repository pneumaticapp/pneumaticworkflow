import React, { useContext, useMemo, useRef, useState } from 'react';
import { IntlShape, useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getEmptyField } from './utils/getEmptyField';
import { KickoffShareForm } from './KickoffShareForm';
import { isKickoffCleared } from './utils/isKickoffCleared';
import { KickoffMenu } from './KickoffMenu';
import { IntlMessages } from '../../IntlMessages';
import { EExtraFieldType, IKickoffClient, IExtraField, ETemplateParts, ITemplateClient } from '../../../types/template';
import { IFieldsetCatalogItem } from '../../../types/fieldset';
import { isArrayWithItems } from '../../../utils/helpers';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { getEmptyKickoff } from '../../../utils/template';
import { useHashLink } from '../../../hooks/useHashLink';
import { useWorkflowNameVariables } from '../TaskForm/utils/getTaskVariables';
import { getFieldsetsCatalogIsLoading } from '../../../redux/selectors/fieldsets';
import { IApplicationState, ETemplateStatus } from '../../../types/redux';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview/FieldsetOutputsPreview';
import { FieldsetIconPicker } from '../TaskOutputFlow/FieldsetIconPicker';
import { MergedOutputRows } from '../TaskOutputFlow/MergedOutputRows';
import {
  buildMergedTaskOutputRows,
  buildRowsWithAddedFieldset,
  buildRowsWithRemovedFieldset,
  createFieldsetBinding,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
  TMergedTaskOutputRow,
} from '../TaskOutputFlow/mergeTaskOutputFlow';
import { InputWithVariables } from '../InputWithVariables';
import { useDatasetOptions } from '../ExtraFields/utils/useDatasetOptions';
import { TemplateFieldContext } from '../useTemplateForm/contexts';

import styles from './KickoffRedux.css';

interface IKickoffReduxProps {
  template?: ITemplateClient;
  intl?: IntlShape;
  accountId?: number;
  templateStatus?: ETemplateStatus;
  setKickoff?(value: IKickoffClient): void;
}

export function KickoffRedux({ template: propsTemplate, intl, accountId: propsAccountId, setKickoff }: IKickoffReduxProps): React.ReactElement {
  const intlContext = useIntl();
  const { formatMessage } = intl ?? intlContext;
  const fieldContext = useContext(TemplateFieldContext);
  const accountIdFromState = useSelector((state: IApplicationState) => state.authUser?.account?.id ?? -1);
  const accountId = propsAccountId ?? accountIdFromState;
  const fieldsetsCatalogLoading = useSelector(getFieldsetsCatalogIsLoading);
  const template = propsTemplate ?? fieldContext?.values;

  if (!template) {
    throw new Error('KickoffRedux must receive a template prop or be used inside the Edit Template form provider');
  }

  const { kickoff, wfNameTemplate } = template;
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const variables = useWorkflowNameVariables(kickoff);
  const datasetOptions = useDatasetOptions(kickoff.fields);
  const mergedRows = useMemo(
    () => buildMergedTaskOutputRows(kickoff.fields || [], kickoff.fieldsets || []),
    [kickoff.fields, kickoff.fieldsets],
  );

  useHashLink([
    {
      element: containerRef,
      hash: ETemplateParts.Share,
      handle: () => {
        setIsOpen(true);
      },
    },
  ]);

  const toggleExpanded = () => {
    setIsOpen(!isOpen);
  };

  const handleChangeKickoff = (newKickoff: IKickoffClient) => {
    if (setKickoff) {
      setKickoff(newKickoff);
      return;
    }

    fieldContext?.setFieldValue('kickoff', newKickoff, false);
  };

  const handleClearKickoff = () => {
    handleChangeKickoff({ ...getEmptyKickoff() });
  };

  const saveOutputOrders = (rows: TMergedTaskOutputRow[], allFields?: IExtraField[]) => {
    const { nextFields, nextFieldsets } = normalizeMergedTaskOutputOrders(rows, allFields ?? kickoff.fields);
    handleChangeKickoff({ ...kickoff, fields: nextFields, fieldsets: nextFieldsets });
  };

  const handleCreateField = (type: EExtraFieldType) => {
    const newField = getEmptyField(type, formatMessage, -1);
    const nextFields = [...kickoff.fields, newField];
    const rows = buildMergedTaskOutputRows(nextFields, kickoff.fieldsets || []);
    saveOutputOrders(rows, nextFields);
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(kickoff.fields, apiName, changedProps);
    handleChangeKickoff({ ...kickoff, fields: newFields });
  };

  const handleAddKickoffFieldset = (fieldsetCatalogItem: IFieldsetCatalogItem) => {
    const newFieldsetBinding = createFieldsetBinding(fieldsetCatalogItem);
    const rows = buildRowsWithAddedFieldset(kickoff.fields, kickoff.fieldsets || [], newFieldsetBinding);
    if (rows) saveOutputOrders(rows);
  };

  const handleRemoveFieldset = (sharedFieldsetId: number) => {
    const rows = buildRowsWithRemovedFieldset(kickoff.fields, kickoff.fieldsets || [], sharedFieldsetId);
    saveOutputOrders(rows);
  };

  const handleDeleteField = (apiName: string) => {
    const nextFields = (kickoff.fields || []).filter((field) => field.apiName !== apiName);
    const rows = buildMergedTaskOutputRows(nextFields, kickoff.fieldsets || []);
    saveOutputOrders(rows, nextFields);
  };

  const handleMoveMergedIndex = (index: number, direction: 'up' | 'down') => {
    const moved = moveMergedRow(mergedRows, index, direction);
    saveOutputOrders(moved);
  };

  const renderKickoffForm = () => {
    const isFormEmpty = !isArrayWithItems(kickoff.fields) && !(kickoff.fieldsets || []).length && !kickoff.description;

    return (
      <>
        <div className={styles['workflow-name-field-container']}>
          <p className={styles['section-title']}>{formatMessage({ id: 'template.kick-off-form-workflow-name' })}</p>

          <InputWithVariables
            listVariables={variables}
            templateVariables={variables}
            showInsertButton
            value={wfNameTemplate || ''}
            onChange={(value: string) => {
              fieldContext?.setFieldValue('wfNameTemplate', value, false);

              return Promise.resolve(value);
            }}
            className={styles['workflow-name-field']}
            toolipText={formatMessage({ id: 'kickoff.workflow-name-tooltip' })}
          />
        </div>

        <p className={styles['kick-off__subtitle']}>
          <IntlMessages id="template.kick-off-form-input-title" />
        </p>

        <div className={styles['components']}>
          {ExtraFieldsMap.map((field) => (
            <ExtraFieldIcon {...field} key={field.id} onClick={() => handleCreateField(field.id)} />
          ))}
          <FieldsetIconPicker
            fieldsetsCatalogLoading={fieldsetsCatalogLoading}
            selectedFieldsetIds={(kickoff.fieldsets || []).map((fieldset) => fieldset.sharedFieldsetId)}
            onSelectFieldset={handleAddKickoffFieldset}
            onRemoveFieldset={handleRemoveFieldset}
          />
        </div>

        {!isFormEmpty && (
          <div className={styles['fields']}>
            <MergedOutputRows
              mergedRows={mergedRows}
              onDeleteField={handleDeleteField}
              onMoveRow={handleMoveMergedIndex}
              onEditField={handleEditField}
              onRemoveFieldset={handleRemoveFieldset}
              datasetOptions={datasetOptions}
              accountId={accountId}
              formatMessage={formatMessage}
            />
          </div>
        )}

        <KickoffShareForm className={styles['share-form']} />
      </>
    );
  };

  const renderKickoffLabels = () => {
    const { fields, fieldsets } = kickoff;
    const hasFieldsetChips = (fieldsets || []).some((fieldset) => isArrayWithItems(fieldset.fields));

    if (!isArrayWithItems(fields) && !hasFieldsetChips) {
      return null;
    }

    return (
      <div
        className={styles['description__short']}
        onClick={toggleExpanded}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            toggleExpanded();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label="Toggle expand"
      >
        {isArrayWithItems(fields) && <ExtraFieldsLabels extraFields={fields} />}
        <FieldsetOutputsPreview fieldsets={fieldsets || []} />
      </div>
    );
  };

  return (
    <div className={styles['kick-off']} ref={containerRef}>
      <KickoffMenu
        isKickoffOpen={isOpen}
        isClearDisabled={isKickoffCleared(kickoff)}
        toggleKickoff={toggleExpanded}
        clearForm={handleClearKickoff}
      />
      <div
        className={styles['header']}
        onClick={toggleExpanded}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            toggleExpanded();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label="Toggle expand"
      >
        <span className={styles['title']}>
          <IntlMessages id="template.kick-off-form-title" />
        </span>
      </div>

      {isOpen ? renderKickoffForm() : renderKickoffLabels()}
    </div>
  );
}
