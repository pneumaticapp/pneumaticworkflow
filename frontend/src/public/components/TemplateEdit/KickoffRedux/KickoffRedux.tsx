import React, { useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getEmptyField } from './utils/getEmptyField';
import { KickoffShareForm } from './KickoffShareForm';
import { isKickoffCleared } from './utils/isKickoffCleared';

import { KickoffMenu } from './KickoffMenu';
import { IntlMessages } from '../../IntlMessages';
import { EMoveDirections, EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldMode, EExtraFieldType, IKickoff, IExtraField, ETemplateParts } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyKickoff } from '../../../utils/template';
import { useHashLink } from '../../../hooks/useHashLink';
import { useWorkflowNameVariables } from '../TaskForm/utils/getTaskVariables';

import styles from './KickoffRedux.css';
import { InputWithVariables } from '../InputWithVariables';
import { useDatasetOptions } from '../ExtraFields/utils/useDatasetOptions';
import { useTemplateField } from '../useTemplateForm';
import { getAccountId } from '../../../redux/selectors/user';
import { KickoffLabels } from './KickoffLabels';

export function KickoffRedux() {
  const { formatMessage } = useIntl();
  const accountId = useSelector(getAccountId);
  const { values, setFieldValue } = useTemplateField();
  const { kickoff, wfNameTemplate } = values;
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const variables = useWorkflowNameVariables(kickoff);
  const datasetOptions = useDatasetOptions(kickoff.fields);

  useHashLink([
    {
      element: containerRef,
      hash: ETemplateParts.Share,
      handle: () => {
        setIsOpen(true);
      },
    },
  ]);

  const getSortedFields = () => {
    return [...kickoff.fields].sort((a, b) => b.order - a.order);
  };

  const toggleExpanded = () => {
    setIsOpen(!isOpen);
  };

  const handleChangeKickoff = (newKickoff: IKickoff) => {
    setFieldValue('kickoff', newKickoff, false);
  };

  const handleClearKickoff = () => {
    const newKickoff = { ...getEmptyKickoff() };
    handleChangeKickoff(newKickoff);
  };

  const handleCreateField = (type: EExtraFieldType) => {
    const newKickoff = {
      ...kickoff,
      fields: getNormalizeFieldsOrders([...kickoff.fields, getEmptyField(type, formatMessage)]),
    };

    handleChangeKickoff(newKickoff!);
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);
    handleChangeKickoff({ ...kickoff, fields: newFields });
  };

  const handleDeleteField = (idx: number) => {
    const newKickoffFields = getSortedFields().filter((_, index) => index !== idx);
    const newOrderedKickoff = {
      ...kickoff,
      fields: getNormalizeFieldsOrders(newKickoffFields),
    };

    handleChangeKickoff(newOrderedKickoff);
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const newKickoffFields = moveWorkflowField(from, to, getSortedFields());

    handleChangeKickoff({
      ...kickoff,
      fields: newKickoffFields,
    });
  };

  const renderKickoffForm = () => {
    const isFormEmpty = !isArrayWithItems(kickoff.fields) && !kickoff.description;

    return (
      <>
        <div className={styles['workflow-name-field-container']}>
          <p className={styles['section-title']}>{formatMessage({ id: 'template.kick-off-form-workflow-name' })}</p>

          <InputWithVariables
            listVariables={variables}
            templateVariables={variables}
            value={wfNameTemplate || ''}
            onChange={(value: string) => {
              setFieldValue('wfNameTemplate', value, false);

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
        </div>

        {!isFormEmpty && (
          <div className={styles['fields']}>
            {getSortedFields().map((field, index) => (
              <ExtraFieldIntl
                key={field.apiName}
                id={index}
                field={field}
                fieldsCount={kickoff.fields.length}
                labelBackgroundColor={EInputNameBackgroundColor.White}
                deleteField={() => handleDeleteField(index)}
                moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
                moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
                editField={handleEditField(field.apiName)}
                mode={EExtraFieldMode.Kickoff}
                datasetOptions={datasetOptions}
                accountId={accountId}
              />
            ))}
          </div>
        )}

        <KickoffShareForm className={styles['share-form']} />
      </>
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

      {isOpen ? renderKickoffForm() : <KickoffLabels fields={kickoff.fields} onToggle={toggleExpanded} />}
    </div>
  );
}
