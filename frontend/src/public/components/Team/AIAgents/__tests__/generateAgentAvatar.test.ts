import { generateAgentAvatar } from '../utils/generateAgentAvatar';

describe('generateAgentAvatar', () => {
  const context = {
    fillStyle: '',
    font: '',
    textAlign: '',
    textBaseline: '',
    fillRect: jest.fn(),
    fillText: jest.fn(),
  };
  const fillStyles: string[] = [];

  beforeEach(() => {
    jest.clearAllMocks();
    fillStyles.length = 0;
    context.fillRect.mockImplementation(() => fillStyles.push(context.fillStyle));
    jest
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(context as unknown as CanvasRenderingContext2D);
    jest.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback: BlobCallback) => {
      callback(new Blob(['png'], { type: 'image/png' }));
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('draws the initials on a random background and returns a png file', async () => {
    jest.spyOn(Math, 'random').mockReturnValue(0.5);

    const file = await generateAgentAvatar('AA');

    expect(fillStyles).toEqual(['hsl(180, 60%, 60%)']);
    expect(context.fillText).toHaveBeenCalledWith('AA', 128, 128);
    expect(file).toBeInstanceOf(File);
    expect(file?.name).toBe('ai-agent-avatar.png');
    expect(file?.type).toBe('image/png');
  });

  it('uses a new background on every call', async () => {
    jest.spyOn(Math, 'random').mockReturnValueOnce(0.1).mockReturnValueOnce(0.9);

    await generateAgentAvatar('AA');
    await generateAgentAvatar('AA');

    expect(fillStyles).toEqual(['hsl(36, 60%, 60%)', 'hsl(324, 60%, 60%)']);
  });

  it('falls back to AI initials when the name is empty', async () => {
    await generateAgentAvatar('');

    expect(context.fillText).toHaveBeenCalledWith('AI', 128, 128);
  });

  it('returns null when the canvas is not available', async () => {
    jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);

    await expect(generateAgentAvatar('AA')).resolves.toBeNull();
  });
});
