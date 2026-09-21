const TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const MAX_FILE_BYTES = 12 * 1024 * 1024;
const MAX_EDGE = 1600;
export const PHOTO_MAX_CHARS = 800000;
export const PHOTO_PATTERN = /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/;

export function isReportPhoto(value) {
  return typeof value === "string" && value.length <= PHOTO_MAX_CHARS && PHOTO_PATTERN.test(value);
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("That photo could not be read."));
    reader.readAsDataURL(file);
  });
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("That photo could not be read."));
    image.src = src;
  });
}

export async function fileToReportPhoto(file) {
  if (!file) return "";
  if (!TYPES.has(file.type)) throw new Error("Choose a JPEG, PNG, or WebP photo.");
  if (file.size > MAX_FILE_BYTES) throw new Error("Choose a photo smaller than 12 MB.");
  const image = await loadImage(await readFile(file));
  const scale = Math.min(1, MAX_EDGE / Math.max(image.width, image.height));
  const width = Math.max(1, Math.round(image.width * scale));
  const height = Math.max(1, Math.round(image.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("That photo could not be prepared.");
  context.drawImage(image, 0, 0, width, height);
  let quality = 0.82;
  let dataUrl = canvas.toDataURL("image/jpeg", quality);
  while (dataUrl.length > PHOTO_MAX_CHARS && quality > 0.4) {
    quality -= 0.12;
    dataUrl = canvas.toDataURL("image/jpeg", quality);
  }
  if (!isReportPhoto(dataUrl)) throw new Error("That photo is too large to save in this browser. Try a smaller image.");
  return dataUrl;
}
