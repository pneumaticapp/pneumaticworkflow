import { generateAgentAvatar } from '../utils/generateAgentAvatar';

describe('generateAgentAvatar', () => {
  const gradient = { addColorStop: jest.fn() };
  const context = {
    fillStyle: '' as unknown,
    globalAlpha: 1,
    filter: '',
    createLinearGradient: jest.fn(() => gradient),
    fillRect: jest.fn(),
    beginPath: jest.fn(),
    arc: jest.fn(),
    fill: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
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

  it('draws a gradient with blurred spots and returns a png file', async () => {
    jest.spyOn(Math, 'random').mockReturnValue(0.5);

    const file = await generateAgentAvatar();

    expect(gradient.addColorStop).toHaveBeenNthCalledWith(1, 0, 'hsl(180, 75%, 62%)');
    expect(gradient.addColorStop).toHaveBeenNthCalledWith(2, 1, 'hsl(240, 75%, 62%)');
    expect(context.fillRect).toHaveBeenCalledWith(0, 0, 256, 256);
    expect(context.fill).toHaveBeenCalledTimes(3);
    expect(context.filter).toBe('blur(25.6px)');
    expect(file).toBeInstanceOf(File);
    expect(file?.name).toBe('ai-agent-avatar.png');
    expect(file?.type).toBe('image/png');
  });

  it('uses a new palette on every call', async () => {
    jest.spyOn(Math, 'random').mockReturnValueOnce(0.1).mockReturnValue(0.5);
    await generateAgentAvatar();
    jest.spyOn(Math, 'random').mockReturnValueOnce(0.9).mockReturnValue(0.5);
    await generateAgentAvatar();

    expect(gradient.addColorStop).toHaveBeenNthCalledWith(1, 0, 'hsl(36, 75%, 62%)');
    expect(gradient.addColorStop).toHaveBeenNthCalledWith(3, 0, 'hsl(324, 75%, 62%)');
  });

  it('returns null when the canvas is not available', async () => {
    jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);

    await expect(generateAgentAvatar()).resolves.toBeNull();
  });
});
