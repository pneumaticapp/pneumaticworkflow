import reducer, {
  loadAiAgents,
  loadAiAgentsSuccess,
  loadAiAgentsFailed,
  createAiAgentSuccess,
  updateAiAgentSuccess,
  deleteAiAgentSuccess,
  openAiAgentModal,
  closeAiAgentModal,
  loadAiConnectionSuccess,
  loadAiConnectionFailed,
  saveAiConnection,
  saveAiConnectionSuccess,
  removeAiConnectionSuccess,
  aiConnectionRequestFailed,
} from '../slice';
import { IAiAgent } from '../types';

const makeAgent = (overrides: Partial<IAiAgent> = {}): IAiAgent => ({
  id: 1,
  name: 'Analyst',
  modelSlug: 'test/model',
  systemPrompt: '',
  temperature: null,
  maxTokens: null,
  photo: null,
  isActive: true,
  ...overrides,
});

describe('aiAgents slice', () => {
  it('loadAiAgents sets loading', () => {
    const state = reducer(undefined, loadAiAgents());

    expect(state.isLoading).toBe(true);
  });

  it('loadAiAgentsSuccess stores the list and marks the feature enabled', () => {
    const agent = makeAgent();

    const state = reducer(undefined, loadAiAgentsSuccess([agent]));

    expect(state.list).toEqual([agent]);
    expect(state.isEnabled).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it('loadAiAgentsFailed clears the list and marks the feature disabled', () => {
    const withAgents = reducer(undefined, loadAiAgentsSuccess([makeAgent()]));

    const state = reducer(withAgents, loadAiAgentsFailed());

    expect(state.list).toEqual([]);
    expect(state.isEnabled).toBe(false);
  });

  it('createAiAgentSuccess appends the agent and closes the modal', () => {
    const opened = reducer(undefined, openAiAgentModal(null));

    const state = reducer(opened, createAiAgentSuccess(makeAgent()));

    expect(state.list).toHaveLength(1);
    expect(state.editModal.isOpen).toBe(false);
  });

  it('updateAiAgentSuccess replaces the agent by id', () => {
    const initial = reducer(undefined, loadAiAgentsSuccess([makeAgent(), makeAgent({ id: 2, name: 'Reviewer' })]));

    const state = reducer(initial, updateAiAgentSuccess(makeAgent({ id: 2, name: 'Auditor' })));

    expect(state.list.find((agent) => agent.id === 2)?.name).toBe('Auditor');
    expect(state.list).toHaveLength(2);
  });

  it('deleteAiAgentSuccess removes the agent by id', () => {
    const initial = reducer(undefined, loadAiAgentsSuccess([makeAgent(), makeAgent({ id: 2 })]));

    const state = reducer(initial, deleteAiAgentSuccess({ id: 1 }));

    expect(state.list).toHaveLength(1);
    expect(state.list[0].id).toBe(2);
  });

  it('openAiAgentModal stores the agent being edited', () => {
    const agent = makeAgent();

    const state = reducer(undefined, openAiAgentModal(agent));

    expect(state.editModal).toEqual({ isOpen: true, editAgent: agent });
  });

  it('closeAiAgentModal resets the modal', () => {
    const opened = reducer(undefined, openAiAgentModal(makeAgent()));

    const state = reducer(opened, closeAiAgentModal());

    expect(state.editModal).toEqual({ isOpen: false, editAgent: null });
  });
});

describe('aiAgents connection slice', () => {
  const connection = { id: 1, baseUrl: 'https://openrouter.ai/api/v1', apiKeyMask: 'sk-or-v1••••cdef' };

  it('loadAiConnectionSuccess marks the endpoint available and stores the value', () => {
    const state = reducer(undefined, loadAiConnectionSuccess(connection));

    expect(state.connection.isAvailable).toBe(true);
    expect(state.connection.value).toEqual(connection);
  });

  it('loadAiConnectionSuccess with null keeps availability without a value', () => {
    const state = reducer(undefined, loadAiConnectionSuccess(null));

    expect(state.connection.isAvailable).toBe(true);
    expect(state.connection.value).toBeNull();
  });

  it('loadAiConnectionFailed hides the connection management', () => {
    const withConnection = reducer(undefined, loadAiConnectionSuccess(connection));

    const state = reducer(withConnection, loadAiConnectionFailed());

    expect(state.connection.isAvailable).toBe(false);
    expect(state.connection.value).toBeNull();
  });

  it('saveAiConnection sets saving, success stores the value', () => {
    const saving = reducer(undefined, saveAiConnection({ apiKey: 'sk-or-v1-secret' }));
    expect(saving.connection.isSaving).toBe(true);

    const state = reducer(saving, saveAiConnectionSuccess(connection));

    expect(state.connection.isSaving).toBe(false);
    expect(state.connection.value).toEqual(connection);
  });

  it('removeAiConnectionSuccess clears the value', () => {
    const withConnection = reducer(undefined, saveAiConnectionSuccess(connection));

    const state = reducer(withConnection, removeAiConnectionSuccess());

    expect(state.connection.value).toBeNull();
  });

  it('aiConnectionRequestFailed resets saving', () => {
    const saving = reducer(undefined, saveAiConnection({ apiKey: 'sk-or-v1-secret' }));

    const state = reducer(saving, aiConnectionRequestFailed());

    expect(state.connection.isSaving).toBe(false);
  });
});
