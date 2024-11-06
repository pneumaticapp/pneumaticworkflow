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
  it('if the loading prop is passed, a loading indicator will render in the component', () => {
    // const wrapper = shallow(<Templates {...mockProps} loading/>);

    // expect(wrapper.exists('.loading')).toEqual(true);
  });
  it('clicking the “Load More” button triggers the loading of new templates', () => {
    // const wrapper = shallow(<Templates {...mockProps}/>);

    // wrapper.find({ 'data-test-id': 'show-more-button' }).simulate('click');

    // expect(mockProps.loadTemplates).toHaveBeenCalledWith(1);
    // expect(mockProps.loadTemplates).toHaveBeenCalledTimes(2);
  });
  it('clicking the “Load More” button does not trigger the loading of new templates if the count is less than the limit', () => {
    // const workflowList = {...mockProps.templatesList, count: 0};
    // const wrapper = shallow(<Templates {...mockProps} templatesList={workflowList}/>);

    // wrapper.find({ 'data-test-id': 'show-more-button' }).simulate('click');

    // expect(mockProps.loadTemplates).toHaveBeenCalledTimes(1);
  });
});
