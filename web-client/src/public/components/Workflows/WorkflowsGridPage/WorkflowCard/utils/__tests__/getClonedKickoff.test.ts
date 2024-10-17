/* eslint-disable */
/* prettier-ignore */
import { IWorkflowDetailsKickoff } from '../../../../../../types/workflow';
import { EExtraFieldType, IKickoff } from '../../../../../../types/template';
import { getClonedKickoff } from '../getClonedKickoff';

const mockWorkflowDetailKickoff: IWorkflowDetailsKickoff = {
  id: 1,
  description: 'Видео youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\nВидео loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\nВидео 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 видео:\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
  output: [
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
    },
    {
      id: 60848,
      type: EExtraFieldType.Checkbox,
      isRequired: false,
      name: 'Checkboxes',
      description: '',
      apiName: 'checkboxes-989',
      value: '',
      selections: [
        {
          id: 27659,
          value: 'value1',
          isSelected: false,
          apiName: 'selection-vin9ak',
        },
        {
          id: 27660,
          value: 'value2',
          isSelected: false,
          apiName: 'selection-6r2pcy',
        },
      ],
      attachments: [],
      order: 3,
    },
    {
      id: 60849,
      type: EExtraFieldType.Radio,
      isRequired: false,
      name: 'Radios',
      description: '',
      apiName: 'radios-990',
      value: '',
      selections: [
        {
          id: 27661,
          value: '1',
          isSelected: false,
          apiName: 'selection-33cchr',
        },
        {
          id: 27662,
          value: '2',
          isSelected: false,
          apiName: 'selection-709cjo',
        },
      ],
      attachments: [],
      order: 2,
    },
  ],
};

const templateKickoffMock: IKickoff = {
  id: 4821,
  description: 'Видео youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\nВидео loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\nВидео 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 видео:\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
  fields: [
    {
      id: 20770,
      type: EExtraFieldType.String,
      name: 'https://www.youtube.com/watch?v=JZRm7NKTPhk',
      description: 'Ilya',
      isRequired: false,
      order: 7,
      apiName: 'string-985',
    },
    {
      id: 20771,
      type: EExtraFieldType.Text,
      name: 'Textarea',
      description: '',
      isRequired: false,
      order: 6,
      apiName: 'textarea-986',
    },
    {
      id: 20772,
      type: EExtraFieldType.Url,
      name: 'Link',
      description: '',
      isRequired: false,
      order: 5,
      apiName: 'link-987',
    },
    {
      id: 20773,
      type: EExtraFieldType.Date,
      name: 'Date',
      description: '',
      isRequired: false,
      order: 4,
      apiName: 'date-988',
    },
    {
      id: 20774,
      type: EExtraFieldType.Checkbox,
      name: 'Checkboxes',
      description: '',
      isRequired: false,
      selections: [
        {
          id: 7227,
          value: 'value1',
          apiName: 'selection-vin9ak',
        },
        {
          id: 7228,
          value: 'value2',
          apiName: 'selection-6r2pcy',
        },
      ],
      order: 3,
      apiName: 'checkboxes-989',
    },
    {
      id: 20775,
      type: EExtraFieldType.Radio,
      name: 'Radios',
      description: '',
      isRequired: false,
      selections: [
        {
          id: 7229,
          value: '1',
          apiName: 'selection-33cchr',
        },
        {
          id: 7230,
          value: '2',
          apiName: 'selection-709cjo',
        },
      ],
      order: 2,
      apiName: 'radios-990',
    },
  ],
};

const expectedKickoff = {
  description: 'Видео youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\nВидео loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\nВидео 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 видео:\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
  fields: [
    {
      id: 60844,
      type: 'string',
      isRequired: false,
      name: 'https://www.youtube.com/watch?v=JZRm7NKTPhk',
      description: 'Ilya',
      apiName: 'string-985',
      value: '',
      selections: [],
      attachments: [],
      order: 7,
    },
    {
      id: 60845,
      type: 'text',
      isRequired: false,
      name: 'Textarea',
      description: '',
      apiName: 'textarea-986',
      value: '',
      selections: [],
      attachments: [],
      order: 6,
    },
    {
      id: 60846,
      type: 'url',
      isRequired: false,
      name: 'Link',
      description: '',
      apiName: 'link-987',
      value: '',
      selections: [],
      attachments: [],
      order: 5,
    },
    {
      id: 60847,
      type: 'date',
      isRequired: false,
      name: 'Date',
      description: '',
      apiName: 'date-988',
      value: '',
      selections: [],
      attachments: [],
      order: 4,
    },
    {
      id: 60848,
      type: 'checkbox',
      isRequired: false,
      name: 'Checkboxes',
      description: '',
      apiName: 'checkboxes-989',
      value: [],
      selections: [
        {
          id: 7227,
          value: 'value1',
          isSelected: false,
          apiName: 'selection-vin9ak',
        },
        {
          id: 7228,
          value: 'value2',
          isSelected: false,
          apiName: 'selection-6r2pcy',
        },
      ],
      attachments: [],
      order: 3,
    },
    {
      id: 60849,
      type: 'radio',
      isRequired: false,
      name: 'Radios',
      description: '',
      apiName: 'radios-990',
      value: null,
      selections: [
        {
          id: 7229,
          value: '1',
          isSelected: false,
          apiName: 'selection-33cchr',
        },
        {
          id: 7230,
          value: '2',
          isSelected: false,
          apiName: 'selection-709cjo',
        },
      ],
      attachments: [],
      order: 2,
    },
  ],
};

describe('getClonedKickoff.', () => {
  it('should work', async () => {
    const clonedKickoff = await getClonedKickoff(mockWorkflowDetailKickoff, templateKickoffMock);

    expect(clonedKickoff).toStrictEqual(expectedKickoff);
  });
});
