import * as React from 'react';
import { useMemo } from 'react';
import { IntlShape } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { getEmptyField } from './utils/getEmptyField';
import { KickoffShareForm } from './KickoffShareForm';
import { isKickoffCleared } from './utils/isKickoffCleared';
import { FieldsetIconPicker } from '../TaskOutputFlow/FieldsetIconPicker';
import {
  buildMergedTaskOutputRows,
  buildRowsWithAddedFieldset,
  buildRowsWithRemovedFieldset,
  createFieldsetBinding,
  moveMergedRow,
  normalizeMergedTaskOutputOrders,
  TMergedTaskOutputRow,
} from '../TaskOutputFlow/mergeTaskOutputFlow';
import { MergedOutputRows } from '../TaskOutputFlow/MergedOutputRows';

import { KickoffMenu } from './KickoffMenu';
import { IntlMessages } from '../../IntlMessages';
import {  EExtraFieldType, IExtraField, ETemplateParts, IKickoffClient, ITemplateClient } from '../../../types/template';
import { IFieldsetCatalogItem } from '../../../types/fieldset';
import { isArrayWithItems } from '../../../utils/helpers';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { ETemplateStatus } from '../../../types/redux';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { getEmptyKickoff } from '../../../utils/template';
import { useHashLink } from '../../../hooks/useHashLink';
import { useWorkflowNameVariables } from '../TaskForm/utils/getTaskVariables';
import { getFieldsetsCatalogByApiName, getFieldsetsCatalogIsLoading } from '../../../redux/selectors/fieldsets';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview/FieldsetOutputsPreview';

import styles from './KickoffRedux.css';
import { patchTemplate } from '../../../redux/actions';
import { InputWithVariables } from '../InputWithVariables';
import { useDatasetOptions } from '../ExtraFields/utils/useDatasetOptions';

export interface IKickoffReduxProps {
  template: ITemplateClient;
  intl: IntlShape;
  accountId: number;
  templateStatus: ETemplateStatus;
  setKickoff(value: IKickoffClient): void;
}

export function KickoffRedux({
  template: { id: templateId, kickoff, wfNameTemplate },
  intl: { formatMessage },
  setKickoff,
  accountId,
}: IKickoffReduxProps) {
  const dispatch = useDispatch();
  const fieldsetsByApiName = useSelector(getFieldsetsCatalogByApiName);
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const variables = useWorkflowNameVariables(kickoff, fieldsetsByApiName);
  const datasetOptions = useDatasetOptions(kickoff.fields);
  const fieldsetsCatalogLoading = useSelector(getFieldsetsCatalogIsLoading);
  
  const mergedRows = useMemo(
    () => buildMergedTaskOutputRows(kickoff.fields || [], kickoff.fieldsets || []),
    [kickoff.fields, kickoff.fieldsets],
  );

  const editTemplate = (templateFields: Partial<ITemplateClient>) => {
    dispatch(patchTemplate({ changedFields: templateFields }));
  };

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
    setKickoff(newKickoff);
  };

  const handleClearKickoff = () => {
    const newKickoff = { ...getEmptyKickoff() };
    setKickoff(newKickoff);
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

  const saveOutputOrders = (rows: TMergedTaskOutputRow[], allFields?: IExtraField[]) => {
    const { nextFields, nextFieldsets } = normalizeMergedTaskOutputOrders(rows, allFields ?? kickoff.fields);
    handleChangeKickoff({ ...kickoff, fields: nextFields, fieldsets: nextFieldsets });
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
    const nextFields = (kickoff.fields || []).filter((f) => f.apiName !== apiName);
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
              editTemplate({
                wfNameTemplate: value,
              });

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
          {ExtraFieldsMap.map((x) => (
            <ExtraFieldIcon {...x} key={x.id} onClick={() => handleCreateField(x.id)} />
          ))}
          <FieldsetIconPicker
            templateId={templateId}
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
    const hasFieldsetChips = (fieldsets || []).some(
      (taskFieldset) => isArrayWithItems(taskFieldset.fields),
    );

    if (!isArrayWithItems(fields) && !hasFieldsetChips) {
      return null;
    }

    return (
      <div
        className={styles['description__short']}
        onClick={toggleExpanded}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
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
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
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
