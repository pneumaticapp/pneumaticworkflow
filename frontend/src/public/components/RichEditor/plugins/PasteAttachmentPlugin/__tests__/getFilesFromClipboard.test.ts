import { getFilesFromClipboard } from '../getFilesFromClipboard';

function createPasteEvent(clipboardData: {
  files?: File[];
  items?: { kind: string; getAsFile: () => File | null }[];
}): ClipboardEvent {
  const dataTransfer = {
    files: createFileList(clipboardData.files ?? []),
    items: clipboardData.items ?? [],
    getData: () => '',
    setData: () => {},
    clearData: () => {},
    setDragImage: () => {},
    dropEffect: 'none',
    effectAllowed: 'none',
    types: [],
  } as unknown as DataTransfer;
  return { clipboardData: dataTransfer } as unknown as ClipboardEvent;
}

function createFileList(files: File[]): FileList {
  const list = Object.assign([...files], { length: files.length });
  return list as unknown as FileList;
}

describe('getFilesFromClipboard', () => {
  it('returns empty array when clipboardData is missing', () => {
    const event = {} as unknown as ClipboardEvent;
    expect(getFilesFromClipboard(event)).toEqual([]);
  });

  it('returns empty array when clipboardData is null', () => {
    const event = { clipboardData: null } as unknown as ClipboardEvent;
    expect(getFilesFromClipboard(event)).toEqual([]);
  });

  it('returns files from clipboardData.files', () => {
    const file = new File(['content'], 'image.png', { type: 'image/png' });
    const event = createPasteEvent({ files: [file] });
    expect(getFilesFromClipboard(event)).toEqual([file]);
  });

  it('returns multiple files from clipboardData.files', () => {
    const file1 = new File(['a'], 'a.png', { type: 'image/png' });
    const file2 = new File(['b'], 'b.jpg', { type: 'image/jpeg' });
    const event = createPasteEvent({ files: [file1, file2] });
    expect(getFilesFromClipboard(event)).toEqual([file1, file2]);
  });

  it('returns empty array when files is empty', () => {
    const event = createPasteEvent({ files: [] });
    expect(getFilesFromClipboard(event)).toEqual([]);
  });

  it('includes files from clipboardData.items when kind is "file"', () => {
    const file = new File(['x'], 'doc.pdf', { type: 'application/pdf' });
    const event = createPasteEvent({
      files: [],
      items: [{ kind: 'file', getAsFile: () => file }],
    });
    expect(getFilesFromClipboard(event)).toEqual([file]);
  });

  it('ignores clipboardData.items when kind is not "file"', () => {
    const event = createPasteEvent({
      files: [],
      items: [
        { kind: 'text/html', getAsFile: () => null },
        { kind: 'text/plain', getAsFile: () => null },
      ],
    });
    expect(getFilesFromClipboard(event)).toEqual([]);
  });

  it('ignores item when getAsFile returns null', () => {
    const event = createPasteEvent({
      files: [],
      items: [{ kind: 'file', getAsFile: () => null }],
    });
    expect(getFilesFromClipboard(event)).toEqual([]);
  });

  it('does not duplicate file when it appears in both files and items', () => {
    const file = new File(['same'], 'same.png', { type: 'image/png' });
    const event = createPasteEvent({
      files: [file],
      items: [{ kind: 'file', getAsFile: () => file }],
    });
    expect(getFilesFromClipboard(event)).toEqual([file]);
  });

  it('combines files from both files and items when different', () => {
    const file1 = new File(['1'], '1.png', { type: 'image/png' });
    const file2 = new File(['2'], '2.jpg', { type: 'image/jpeg' });
    const event = createPasteEvent({
      files: [file1],
      items: [{ kind: 'file', getAsFile: () => file2 }],
    });
    expect(getFilesFromClipboard(event)).toEqual([file1, file2]);
  });
});
