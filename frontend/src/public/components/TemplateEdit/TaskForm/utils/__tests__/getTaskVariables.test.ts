import { EExtraFieldType, IKickoff, ITemplateTask } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { TTaskVariable } from '../../../types';
import { getTaskVariables } from '../getTaskVariables';

const mockKikoff: IKickoff = {
  description: 'Kickoff description',
  fields: [
    {
      name: 'Client name',
      type: EExtraFieldType.String,
      isRequired: false,
      description: 'Enter client name',
      apiName: 'client-name-3967',
      selections: [],
      order: 1,
      userId: null,
      groupId: null,
    },
  ],
};

const mockTask1: ITemplateTask = {
  id: 3048,
  apiName: 'task-1',
  name: 'Task 1',
  description: "Check data on correct. If it's not - requesting for actualisation to user.",
  number: 1,
  rawPerformers: [],
  requireCompletionByAll: true,
  fields: [
    {
      name: 'Large Text Field',
      type: EExtraFieldType.Text,
      isRequired: false,
      description: '',
      apiName: 'large-text-field-8622',
      selections: [],
      order: 0,
      userId: null,
      groupId: null,
    },
  ],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: '5f6cbe6b-238e-462e-8f18-d5ee5ec45de3',
  checklists: [],
  revertTask: null,
  ancestors: [],
};

const mockTask2: ITemplateTask = {
  id: 3049,
  apiName: 'task-2',
  name: 'Task2',
  description: 'Checking is request actual, and that occurence repeating',
  number: 2,
  rawPerformers: [],
  requireCompletionByAll: false,
  fields: [
    {
      name: 'Reasons',
      type: EExtraFieldType.Text,
      isRequired: true,
      description: 'Enter reasons of client requesting',
      apiName: 'reasons-3969',
      selections: [],
      order: 0,
      userId: null,
      groupId: null,
    },
  ],
  delay: null,
  rawDueDate: createEmptyTaskDueDate(),
  conditions: [],
  uuid: '86b7e716-3819-4b2b-b306-749e0ac2f4e9',
  checklists: [],
  revertTask: null,
  ancestors: ['task-1'],
};

describe('getTaskVariables', () => {
  it("correctly gets 1st task's variables", () => {
    const tasks: ITemplateTask[] = [mockTask1, mockTask2];
    const expectedFirstTaskVariables: TTaskVariable[] = [
      {
        apiName: 'client-name-3967',
        title: 'Client name',
        subtitle: 'Kick-off form',
        richSubtitle: 'Kick-off form',
        selections: [],
        type: EExtraFieldType.String,
      },
    ];

    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask1);
    const expectedResult = expectedFirstTaskVariables;

    expect(actualResult).toStrictEqual(expectedResult);
  });

  it("correctly gets 2nd task's variables", () => {
    const tasks: ITemplateTask[] = [mockTask1, mockTask2];
    const expectedSecondTaskVariables: TTaskVariable[] = [
      {
        apiName: 'client-name-3967',
        title: 'Client name',
        subtitle: 'Kick-off form',
        richSubtitle: 'Kick-off form',
        selections: [],
        type: EExtraFieldType.String,
      },
      {
        apiName: 'large-text-field-8622',
        title: 'Large Text Field',
        subtitle: 'Task 1',
        richSubtitle: 'Task 1',
        selections: [],
        type: EExtraFieldType.Text,
      },
    ];

    const actualResult = getTaskVariables(mockKikoff, tasks, mockTask2);
    const expectedResult = expectedSecondTaskVariables;

    expect(actualResult).toStrictEqual(expectedResult);
  });
});
