/* eslint-disable no-plusplus */
export function base64ToBlob(base64Str: string): Blob {
  // convert base64 to raw binary data held in a string
  // doesn't handle URLEncoded DataURIs - see StackOverflow answer #6850276 for code that does this
  const byteString = atob(base64Str.split(',')[1]);

  // separate out the mime component
  const mimeString = base64Str.split(',')[0].split(':')[1].split(';')[0];

  // write the bytes of the string to an ArrayBuffer
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }

  // write the ArrayBuffer to a blob, and you're done
  const bb = new Blob([ab], { type: mimeString });

  return bb;
}
