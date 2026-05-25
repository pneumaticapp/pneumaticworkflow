export function getFilesFromClipboard(event: ClipboardEvent): File[] {
  const dataTransfer = event.clipboardData;
  if (!dataTransfer) return [];

  const files: File[] = [];

  if (dataTransfer.files?.length) {
    files.push(...Array.from(dataTransfer.files));
  }

  if (dataTransfer.items?.length) {
    for (let i = 0; i < dataTransfer.items.length; i += 1) {
      const item = dataTransfer.items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file && !files.includes(file)) {
          files.push(file);
        }
      }
    }
  }

  return files;
}
