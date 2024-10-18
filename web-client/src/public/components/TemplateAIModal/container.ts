import { connect } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import {
  generateAITemplate,
  stopAITemplateGeneration,
  setIsAITemplateModalOpened,
  applyAITemplate,
  setAITemplateGenerationStatus,
} from '../../redux/actions';

import { ITemplateAIModalProps, TemplateAIModal } from './TemplateAIModal';

export type TStoreProps = Pick<
ITemplateAIModalProps,
| 'isOpen'
| 'generationStatus'
| 'generatedTemplate'
>;

export type TDispatchProps = Pick<
ITemplateAIModalProps,
| 'setIsModalOpened'
| 'generateTemplate'
| 'stopTemplateGeneration'
| 'applyTemplate'
| 'setTemplateGenerationStatus'
>;

const mapStateToProps = ({
  template,
}: IApplicationState): TStoreProps => {

  return {
    isOpen: template.AITemplate.isModalOpened,
    generationStatus: template.AITemplate.generationStatus,
    generatedTemplate: template.AITemplate.generatedData,
  };
};

const mapDispatchToProps: TDispatchProps = {
  generateTemplate: generateAITemplate,
  stopTemplateGeneration: stopAITemplateGeneration,
  setIsModalOpened: setIsAITemplateModalOpened,
  applyTemplate: applyAITemplate,
  setTemplateGenerationStatus: setAITemplateGenerationStatus,
};

export const TemplateAIModalContainer = connect(mapStateToProps, mapDispatchToProps)(TemplateAIModal);
