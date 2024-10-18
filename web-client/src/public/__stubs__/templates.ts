import { ITaskCommentItem } from '../types/workflow';
import { ITemplate, ITemplateListItem } from '../types/template';
import { getEmptyKickoff } from '../utils/template';

export const templatesList: ITemplateListItem[] = [
  {
    id: 1,
    name: 'Intelligence additional customer information',
    tasksCount: 3,
    performersCount: 1,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
  {
    id: 2,
    name: 'Onboarding new employee',
    tasksCount: 7,
    performersCount: 3,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
  {
    id: 3,
    name: 'Reporting to all employees at the same time',
    tasksCount: 3,
    performersCount: 4,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
  {
    id: 4,
    name: 'Onboarding new client',
    tasksCount: 7,
    performersCount: 1,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
  {
    id: 5,
    name: 'Request for an employee to purchase new equipment',
    tasksCount: 3,
    performersCount: 2,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
  {
    id: 6,
    name: 'Create new blank process',
    tasksCount: 0,
    performersCount: 2,
    templateOwners: [],
    kickoff: null,
    isActive: true,
    isPublic: false,
  },
];

const DEFAULT_TEMPLATE: ITemplate = {
  id: 1,
  name: 'Customer study process',
  description: '',
  finalizable: true,
  isActive: true,
  templateOwners: [],
  tasks: [],
  kickoff: getEmptyKickoff(),
  dateUpdated: '2020-11-18T07:05:56.518930Z',
  updatedBy: 2,
  isPublic: false,
  publicUrl: null,
  publicSuccessUrl: null,
  isEmbedded: false,
  embedUrl: null,
  wfNameTemplate: null,
};

export const mockComments: Array<ITaskCommentItem> = [
  {
    author: {
      id: 1,
    },
    text: 'Nullam id ipsum et libero aliquet aliquet.',
    dateCreated: 'Jul 10, 07:28pm',
    type: 1,
    attachments: [],
  },
  {
    author: {
      id: 2,
    },
    attachments: [],
    text: 'yes',
    dateCreated: 'Jul 9, 01:28pm',
    type: 0,
  },
];

export const getTemplate = (id: string): ITemplate => {
  const listItem = templatesList.find((process) => String(process.id) === id);

  return {
    ...DEFAULT_TEMPLATE,
    ...(listItem as unknown as ITemplate),
  };
};
