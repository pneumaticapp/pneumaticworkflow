// import React from 'react';
// import { shallow } from 'enzyme';

// import { Templates, ITemplatesProps } from '../Templates';
// import { ETemplatesSorting } from '../../../types/workflow';

// const mockProps: ITemplatesProps = {
//   templatesList: {
//     count: 5,
//     offset: 0,
//     items: [{
//       id: 1,
//       isActive: true,
//       name: 'Test Workflow',
//       tasksCount: 5,
//       performersCount: 1,
//       kickoff: null,
//       templateOwners: [1, 2],
//       isPublic: false,
//     }],
//   },
//   systemTemplates: {
//     isLoading: true,
//     items: [],
//     categories: [],
//     filter: {
//       searchText: '',
//       category: null,
//     },
//   },
//   canEdit: true,
//   templatesListSorting: ETemplatesSorting.DateDesc,
//   loadTemplates: jest.fn(),
//   loadTemplatesSystem: jest.fn(),
//   loadTemplatesSystemCategories: jest.fn(),
//   resetTemplates: jest.fn(),
//   openRunWorkflowModal: jest.fn(),
//   cloneTemplate: jest.fn(),
//   deleteTemplate: jest.fn(),
//   setIsAITemplateModalOpened: jest.fn(),
//   changeTemplatesSystemFilter:  jest.fn(),
// };

describe('Templates', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });
  it('если передать пропс loading, то в компоненте отрендерится индикатор загрузки', () => {
    // const wrapper = shallow(<Templates {...mockProps} loading/>);

    // expect(wrapper.exists('.loading')).toEqual(true);
  });
  it('при клике на кнопку загрузить ещё вызывает загрузку новых шаблонов', () => {
    // const wrapper = shallow(<Templates {...mockProps}/>);

    // wrapper.find({ 'data-test-id': 'show-more-button' }).simulate('click');

    // expect(mockProps.loadTemplates).toHaveBeenCalledWith(1);
    // expect(mockProps.loadTemplates).toHaveBeenCalledTimes(2);
  });
  it('при клике на кнопку загрузить ещё не вызывает загрузку новых шаблонов, если count меньше', () => {
    // const workflowList = {...mockProps.templatesList, count: 0};
    // const wrapper = shallow(<Templates {...mockProps} templatesList={workflowList}/>);

    // wrapper.find({ 'data-test-id': 'show-more-button' }).simulate('click');

    // expect(mockProps.loadTemplates).toHaveBeenCalledTimes(1);
  });
});
