/* eslint-disable */
/* prettier-ignore */
import { reducer, INIT_STATE } from '../reducer';
import { TRunWorkflowModalActions, openRunWorkflowModal } from '../actions';
import { IKickoff, EExtraFieldType } from '../../../types/template';

describe('runWorkflowModal reducer', () => {
  it('return default state', () => {
    const result = reducer(undefined, 'NOT_ACTION' as unknown as TRunWorkflowModalActions);

    expect(result).toEqual(INIT_STATE);
  });
  it('openRunWorkflowModal open modal window', () => {
    const runnableWorkflow = {
      id: 4654,
      name: 'End Template',
      kickoff: {
        id: 5129,
        description: '',
        fields: [],
      },
      description: '12346789',
      performersCount: 2,
      tasksCount: 5,
      wfNameTemplate: '',
    };

    const kickoff: IKickoff = {
      description:
        'youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\n loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\n 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 :\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
      fields: [
        {
          id: 60844,
          type: EExtraFieldType.String,
          isRequired: false,
          name: 'https://www.youtube.com/watch?v=JZRm7NKTPhk',
          description: 'Ilya',
          apiName: 'string-985',
          value: '',
          selections: [],
          attachments: [],
          order: 7,
          userId: null,
          groupId: null,
        },
        {
          id: 60845,
          type: EExtraFieldType.Text,
          isRequired: false,
          name: 'Textarea',
          description: '',
          apiName: 'textarea-986',
          value: '',
          selections: [],
          attachments: [],
          order: 6,
          userId: null,
          groupId: null,
        },
        {
          id: 60846,
          type: EExtraFieldType.Url,
          isRequired: false,
          name: 'Link',
          description: '',
          apiName: 'link-987',
          value: '',
          selections: [],
          attachments: [],
          order: 5,
          userId: null,
          groupId: null,
        },
        {
          id: 60847,
          type: EExtraFieldType.Date,
          isRequired: false,
          name: 'Date',
          description: '',
          apiName: 'date-988',
          value: '',
          selections: [],
          attachments: [],
          order: 4,
          userId: null,
          groupId: null,
        },
        {
          id: 60848,
          type: EExtraFieldType.Checkbox,
          isRequired: false,
          name: 'Checkboxes',
          description: '',
          apiName: 'checkboxes-989',
          value: [],
          selections: [
            {
              value: 'value1',
              isSelected: false,
              apiName: 'selection-vin9ak',
            },
            {
              value: 'value2',
              isSelected: false,
              apiName: 'selection-6r2pcy',
            },
          ],
          attachments: [],
          order: 3,
          userId: null,
          groupId: null,
        },
        {
          id: 60849,
          type: EExtraFieldType.Radio,
          isRequired: false,
          name: 'Radios',
          description: '',
          apiName: 'radios-990',
          value: null,
          selections: [
            {
              value: '1',
              isSelected: false,
              apiName: 'selection-33cchr',
            },
            {
              value: '2',
              isSelected: false,
              apiName: 'selection-709cjo',
            },
          ],
          attachments: [],
          order: 2,
          userId: null,
          groupId: null,
        },
      ],
    };

    const action = openRunWorkflowModal({
      ...runnableWorkflow,
      name: '1',
      kickoff,
    });

    const result = reducer(INIT_STATE, action);

    expect(result.isOpen).toEqual(true);
  });
});
