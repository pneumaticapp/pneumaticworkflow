export function getImageDimensions(file: File | Blob): Promise<{ width: number, height: number }> {
  return new Promise((resolve, reject) => {
    const fr = new FileReader;

    fr.onload = () => {
      const img = new Image;

      img.onload = () => {
        const { width, height } = img;

        resolve({ width, height });
      };

      img.onerror = () => {
        reject(new Error('Invalid file type'));
      };

      img.src = fr.result as string;

    };

    fr.readAsDataURL(file);
  });
}