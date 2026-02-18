import React, { useState } from 'react';
import { useIntl } from 'react-intl';
import { debounce } from 'throttle-debounce';
import { useDispatch, useSelector } from 'react-redux';
import StickyBox from 'react-sticky-box';

import { EditableText } from '../../UI';
import { NAVBAR_HEIGHT } from '../../../constants/defaultValues';
import { getTemplateData } from '../../../redux/selectors/template';
import { saveTemplate, setTemplate, setTemplateStatus } from '../../../redux/actions';
import { ETemplateStatus } from '../../../types/redux';
import { ITemplate } from '../../../types/template';
import { TemplateControllsContainer } from '../TemplateControlls';
import { isArrayWithItems } from '../../../utils/helpers';
import { IInfoWarningProps, InfoWarningsModal } from '../InfoWarningsModal';
import { TemplateLastUpdateInfo } from '../TemplateLastUpdateInfo';
import { RichEditor } from '../../RichEditor';

import styles from './TemplateSettings.css';

export function TemplateSettings() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const template = useSelector(getTemplateData);
  const [isInfoWarningsModaOpen, setIsInfoWarningsModaOpen] = useState(false);
  const [infoWarnings, setInfoWarnings] = useState<any>([]);

  const handleChangeTemplateField = (field: keyof ITemplate) => (value: ITemplate[keyof ITemplate]) => {
    const workflow = template;
    let newWorkflow: ITemplate;
    dispatch(setTemplateStatus(ETemplateStatus.Saving));

    if (field === 'isActive') {
      newWorkflow = {
        ...workflow,
        isActive: value as boolean,
      };
    } else {
      newWorkflow = {
        ...workflow,
        [field]: value,
        isActive: false,
      };
    }

    dispatch(setTemplate(newWorkflow));
    submitDebounced();
  };

  const handleChangeTextField = (field: keyof ITemplate) => (value: string) => handleChangeTemplateField(field)(value);

  const submitDebounced = debounce(350, () => dispatch(saveTemplate()));

  const handleSetInfoWarnings = (infoWarningsLocal: ((props: IInfoWarningProps) => JSX.Element)[]) => {
    if (isArrayWithItems(infoWarningsLocal)) {
      setIsInfoWarningsModaOpen(true);
      setInfoWarnings(infoWarningsLocal);
    }
  };

  const renderInfoWarningsModal = () => {
    const handleCloseModal = () => setIsInfoWarningsModaOpen(false);

    return <InfoWarningsModal isOpen={isInfoWarningsModaOpen} onClose={handleCloseModal} warnings={infoWarnings} />;
  };

  return (
    <>
      {renderInfoWarningsModal()}
      <StickyBox offsetTop={NAVBAR_HEIGHT} offsetBottom={20}>
        <EditableText
          text={template.name}
          className={styles['template-name']}
          onChangeText={handleChangeTextField('name')}
          placeholder={formatMessage({ id: 'template.name-placeholder' })}
          editButtonHint={formatMessage({ id: 'template.edit-name' })}
        />
        <div className={styles['description']}>
          <RichEditor
            withToolbar={false}
            placeholder={formatMessage({ id: 'template.placeholder' })}
            className={styles['description-editor']}
            defaultValue={template.description}
            handleChange={(value) => {
              handleChangeTextField('description')(value);
              return Promise.resolve(value);
            }}
          />
        </div>

        <TemplateControllsContainer setInfoWarnings={handleSetInfoWarnings} />

        {(template.updatedBy || template.dateUpdated) && (
          <div className={styles['last-update']}>
            <TemplateLastUpdateInfo updatedBy={template.updatedBy} dateUpdated={template.dateUpdated} />
          </div>
        )}
      </StickyBox>
    </>
  );
}
