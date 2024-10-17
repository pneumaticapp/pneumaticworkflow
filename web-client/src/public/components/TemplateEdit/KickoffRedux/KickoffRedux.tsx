/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { IntlShape } from 'react-intl';

import { getEmptyField } from './utils/getEmptyField';
import { KickoffShareForm } from './KickoffShareForm';
import { isKickoffCleared } from './utils/isKickoffCleared';

import { KickoffMenu } from './KickoffMenu';
import { IntlMessages } from '../../IntlMessages';
import { EMoveDirections, EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldType, IKickoff, IExtraField, ITemplate, ETemplateParts } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';
import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { ETemplateStatus } from '../../../types/redux';
import { ExtraFieldsLabels } from '../ExtraFields/utils/ExtraFieldsLabels';
import { getEmptyKickoff } from '../../../utils/template';
import { useHashLink } from '../../../hooks/useHashLink';
import { useWorkflowNameVariables } from '../TaskForm/utils/getTaskVariables';

import styles from './KickoffRedux.css';
import { useDispatch } from 'react-redux';
import { patchTemplate } from '../../../redux/actions';
import { InputWithVariables } from '../InputWithVariables';

export interface IKickoffReduxProps {
  template: ITemplate;
  intl: IntlShape;
  accountId: number;
  templateStatus: ETemplateStatus;
  setKickoff(value: IKickoff): void;
}

export function KickoffRedux(props: IKickoffReduxProps) {
  const dispatch = useDispatch();
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const { intl: { formatMessage } } = props;

  const variables = useWorkflowNameVariables(props.template.kickoff);

  const editTemplate = (templateFields: Partial<ITemplate>) => {
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

  const getSortedFields = () => {
    const {
      template: { kickoff },
    } = props;

    return [...kickoff.fields].sort((a, b) => b.order - a.order);
  };

  const toggleExpanded = () => {
    setIsOpen(!isOpen);
  };

  const handleChangeKickoff = (newKickoff: IKickoff) => {
    const { setKickoff } = props;

    setKickoff(newKickoff);
  };

  const handleClearKickoff = () => {
    const {
      setKickoff,
      template: { kickoff },
    } = props;

    const newKickoff = { ...getEmptyKickoff(), id: kickoff.id };
    setKickoff(newKickoff);
  };

  const handleCreateField = (type: EExtraFieldType) => {
    const {
      template: { kickoff },
    } = props;

    const newKickoff = {
      ...kickoff,
      fields: getNormalizeFieldsOrders([...kickoff.fields, getEmptyField(type, formatMessage)]),
    };

    handleChangeKickoff(newKickoff!);
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const {
      template: { kickoff },
    } = props;

    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);

    handleChangeKickoff({ ...kickoff, fields: newFields });
  };

  const handleDeleteField = (idx: number) => {
    const {
      template: { kickoff },
    } = props;

    const newKickoffFields = getSortedFields().filter((_, index) => index !== idx);

    const newOrderedKickoff = {
      ...kickoff,
      fields: getNormalizeFieldsOrders(newKickoffFields),
    };

    handleChangeKickoff(newOrderedKickoff);
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const {
      template: { kickoff },
    } = props;

    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;

    const newKickoffFields = moveWorkflowField(from, to, getSortedFields());

    handleChangeKickoff({
      ...kickoff,
      fields: newKickoffFields,
    });
  };

  const renderKickoffForm = () => {
    const {
      template: { kickoff },
      accountId,
    } = props;

    const isFormEmpty = !isArrayWithItems(kickoff.fields) && !kickoff.description;

    return (
      <>
        <div className={styles['workflow-name-field-container']}>
          <p className={styles['section-title']}>
            {formatMessage({ id: 'template.kick-off-form-workflow-name' })}
          </p>

          <InputWithVariables
            listVariables={variables}
            templateVariables={variables}
            value={props.template.wfNameTemplate || ''}
            onChange={(value) => {
              editTemplate({
                wfNameTemplate: value,
              });

              return Promise.resolve(value);
            }}
            className={styles['workflow-name-field']}
            toolipText={formatMessage({ id: 'kickoff.workflow-name-tooltip' })}
            size="lg"
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
                key={index}
                id={index}
                field={field}
                fieldsCount={kickoff.fields.length}
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

        <KickoffShareForm className={styles['share-form']} />
      </>
    );
  };

  const renderKickoffLabels = () => {
    const {
      template: {
        kickoff: { fields },
      },
    } = props;

    if (!isArrayWithItems(fields)) {
      return null;
    }

    return (
      <div className={styles['description__short']} onClick={toggleExpanded}>
        <ExtraFieldsLabels extraFields={fields} />
      </div>
    );
  };

  const {
    template: { kickoff },
  } = props;

  return (
    <div className={styles['kick-off']} ref={containerRef}>
      <KickoffMenu
        isKickoffOpen={isOpen}
        isClearDisabled={isKickoffCleared(kickoff)}
        toggleKickoff={toggleExpanded}
        clearForm={handleClearKickoff}
      />
      <div className={styles['header']} onClick={toggleExpanded}>
        <span className={styles['title']}>
          <IntlMessages id="template.kick-off-form-title" />
        </span>
      </div>

      {isOpen ? renderKickoffForm() : renderKickoffLabels()}
    </div>
  );
}
