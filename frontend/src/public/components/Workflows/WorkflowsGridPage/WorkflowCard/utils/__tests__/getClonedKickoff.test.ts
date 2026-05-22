import { IWorkflowDetailsKickoff } from '../../../../../../types/workflow';
import { EExtraFieldType, IKickoff } from '../../../../../../types/template';
import { getClonedKickoff } from '../getClonedKickoff';

const mockWorkflowDetailKickoff: IWorkflowDetailsKickoff = {
  id: 1,
  description:
    'youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\n loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\n 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 :\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
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
      value: '',
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
      value: '',
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

const templateKickoffMock: IKickoff = {
  description:
    ' youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\n loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\n 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 :\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
  fields: [
    {
      id: 20770,
      type: EExtraFieldType.String,
      name: 'https://www.youtube.com/watch?v=JZRm7NKTPhk',
      description: 'Ilya',
      isRequired: false,
      order: 7,
      apiName: 'string-985',
      userId: null,
      groupId: null,
    },
    {
      id: 20771,
      type: EExtraFieldType.Text,
      name: 'Textarea',
      description: '',
      isRequired: false,
      order: 6,
      apiName: 'textarea-986',
      userId: null,
      groupId: null,
    },
    {
      id: 20772,
      type: EExtraFieldType.Url,
      name: 'Link',
      description: '',
      isRequired: false,
      order: 5,
      apiName: 'link-987',
      userId: null,
      groupId: null,
    },
    {
      id: 20773,
      type: EExtraFieldType.Date,
      name: 'Date',
      description: '',
      isRequired: false,
      order: 4,
      apiName: 'date-988',
      userId: null,
      groupId: null,
    },
    {
      id: 20774,
      type: EExtraFieldType.Checkbox,
      name: 'Checkboxes',
      description: '',
      isRequired: false,
      selections: [
        {
          value: 'value1',
          apiName: 'selection-vin9ak',
        },
        {
          value: 'value2',
          apiName: 'selection-6r2pcy',
        },
      ],
      order: 3,
      apiName: 'checkboxes-989',
      userId: null,
      groupId: null,
    },
    {
      id: 20775,
      type: EExtraFieldType.Radio,
      name: 'Radios',
      description: '',
      isRequired: false,
      selections: [
        {
          value: '1',
          apiName: 'selection-33cchr',
        },
        {
          value: '2',
          apiName: 'selection-709cjo',
        },
      ],
      order: 2,
      apiName: 'radios-990',
      userId: null,
      groupId: null,
    },
  ],
  fieldsets: [],
};

const expectedKickoff = {
  description:
    'youtube: \nhttps://www.youtube.com/watch?v=JZRm7NKTPhk\n loom:\nhttps://www.loom.com/share/29f210bc12484eaa81ca462381fb4415?t=0\n 404 loom:\n\nhttps://www.loom.com/share/9853f0790ad2408094a3717bfcf4a0c0\nYoutube 404 :\n\nhttps://www.youtube.com/watch?v=D6hIeqZt22g',
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
      userId: null,
      groupId: null,
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
      userId: null,
      groupId: null,
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
      userId: null,
      groupId: null,
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
      userId: null,
      groupId: null,
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
        'value1',
        'value2',
      ],
      attachments: [],
      order: 3,
      userId: null,
      groupId: null,
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
        '1',
        '2',
      ],
      attachments: [],
      order: 2,
      userId: null,
      groupId: null,
    },
  ],
  fieldsets: [],
};

describe('getClonedKickoff.', () => {
  it('should work', async () => {
    const clonedKickoff = await getClonedKickoff(mockWorkflowDetailKickoff, templateKickoffMock);

    expect(clonedKickoff).toStrictEqual(expectedKickoff);
  });

  describe('Fieldsets', () => {
    it('does not carry over fieldsets from workflowKickoff into the result (fieldsets=[])', async () => {
      const workflowWithFieldsets: IWorkflowDetailsKickoff = {
        id: 2,
        description: '',
        output: [],
        fieldsets: [
          {
            id: 10,
            apiName: 'fs-1',
            name: 'Fieldset 1',
            description: '',
            order: 0,
            fields: [
              {
                apiName: 'fs-field-1',
                name: 'FS Field',
                type: EExtraFieldType.String,
                value: 'data',
                order: 0,
                userId: null,
                groupId: null,
              },
            ],
          },
        ],
      };

      const emptyTemplateKickoff: IKickoff = {
        description: '',
        fields: [],
        fieldsets: [],
      };

      const result = await getClonedKickoff(workflowWithFieldsets, emptyTemplateKickoff);

      expect(result.fieldsets).toEqual([]);
      expect(result.fields).toEqual([]);
    });

    it('drops workflow fields that are absent in the template', async () => {
      const workflowKickoff: IWorkflowDetailsKickoff = {
        id: 3,
        description: '',
        output: [
          {
            apiName: 'exists-in-both',
            name: 'Both',
            type: EExtraFieldType.String,
            value: 'keep',
            order: 0,
            userId: null,
            groupId: null,
          },
          {
            apiName: 'only-in-workflow',
            name: 'Orphan',
            type: EExtraFieldType.String,
            value: 'drop',
            order: 1,
            userId: null,
            groupId: null,
          },
        ],
      };

      const templateKickoff: IKickoff = {
        description: '',
        fields: [
          {
            apiName: 'exists-in-both',
            name: 'Both',
            type: EExtraFieldType.String,
            order: 0,
            userId: null,
            groupId: null,
          },
        ],
        fieldsets: [],
      };

      const result = await getClonedKickoff(workflowKickoff, templateKickoff);

      expect(result.fields).toHaveLength(1);
      expect(result.fields[0].apiName).toBe('exists-in-both');
      expect(result.fields[0].value).toBe('keep');
    });

    it('filters checkbox value by template selections', async () => {
      const workflowKickoff: IWorkflowDetailsKickoff = {
        id: 4,
        description: '',
        output: [
          {
            apiName: 'cb-1',
            name: 'CB',
            type: EExtraFieldType.Checkbox,
            value: 'a, b, c',
            selections: [],
            order: 0,
            userId: null,
            groupId: null,
          },
        ],
      };

      const templateKickoff: IKickoff = {
        description: '',
        fields: [
          {
            apiName: 'cb-1',
            name: 'CB',
            type: EExtraFieldType.Checkbox,
            selections: ['a', 'c', 'd'],
            order: 0,
            userId: null,
            groupId: null,
          },
        ],
        fieldsets: [],
      };

      const result = await getClonedKickoff(workflowKickoff, templateKickoff);

      expect(result.fields).toHaveLength(1);
      expect(result.fields[0].value).toEqual(['a', 'c']);
      expect(result.fields[0].selections).toEqual(['a', 'c', 'd']);
    });
  });
});
