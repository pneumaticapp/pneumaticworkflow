import { generateAgentAvatar } from '../utils/generateAgentAvatar';

describe('generateAgentAvatar', () => {
  const context = { fillStyle: '', fillRect: jest.fn(), drawImage: jest.fn() };
  const OriginalImage = window.Image;
  let loadedSources: string[];

  beforeEach(() => {
    loadedSources = [];
    jest
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(context as unknown as CanvasRenderingContext2D);
    jest.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback: BlobCallback) => {
      callback(new Blob(['png'], { type: 'image/png' }));
    });
    window.Image = jest.fn(() => {
      const image = {} as HTMLImageElement;
      Object.defineProperty(image, 'src', {
        set: (src: string) => {
          loadedSources.push(src);
          image.onload?.(new Event('load'));
        },
      });
      return image;
    }) as unknown as typeof Image;
  });

  afterEach(() => {
    window.Image = OriginalImage;
    jest.restoreAllMocks();
  });

  it('draws the DiceBear face for the seed and returns a png file', async () => {
    const file = await generateAgentAvatar('agent-seed');

    expect(decodeURIComponent(loadedSources[0])).toContain('data-seed="agent-seed"');
    expect(context.fillRect).toHaveBeenCalledWith(0, 0, 256, 256);
    expect(context.drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, 256, 256);
    expect(file?.name).toBe('ai-agent-avatar.png');
    expect(file?.type).toBe('image/png');
  });

  it('uses a new random seed on every call', async () => {
    await generateAgentAvatar();
    await generateAgentAvatar();

    expect(loadedSources[0]).not.toBe(loadedSources[1]);
  });

  it('returns null without a canvas context', async () => {
    (HTMLCanvasElement.prototype.getContext as jest.Mock).mockReturnValue(null);

    await expect(generateAgentAvatar()).resolves.toBeNull();
  });
});
