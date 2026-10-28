import { generateAgentAvatar } from '../utils/generateAgentAvatar';

const readFile = (file: File) =>
  new Promise<string>((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsText(file);
  });

describe('generateAgentAvatar', () => {
  it('returns a DiceBear svg file for the given seed', async () => {
    const file = generateAgentAvatar('agent-seed');

    expect(file.name).toBe('ai-agent-avatar.svg');
    expect(file.type).toBe('image/svg+xml');
    expect(await readFile(file)).toBe('<svg data-seed="agent-seed"></svg>');
  });

  it('uses a new random seed on every call', async () => {
    const [first, second] = await Promise.all([readFile(generateAgentAvatar()), readFile(generateAgentAvatar())]);

    expect(first).not.toBe(second);
  });
});
