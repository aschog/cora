/** Reading the words out of an image, in the browser the image was added in.
 *
 *  Tesseract compiled to WebAssembly, fetched the first time a photo is added and kept
 *  for the rest of the session. The image is never uploaded: what can leave this
 *  browser is the text, and only once the reader has saved it.
 */

/** One host, pinned: the script, its WebAssembly core and the trained data. */
const CDN = 'https://cdn.jsdelivr.net'
const READER = `${CDN}/npm/tesseract.js@7.0.0/dist/tesseract.min.js`
const WORKER = `${CDN}/npm/tesseract.js@7.0.0/dist/worker.min.js`
const CORE = `${CDN}/npm/tesseract.js-core@7.0.0`
const DATA = `${CDN}/gh/naptha/tessdata@gh-pages/4.0.0`

/** The languages a reading is run with. Trained data is fetched per language, so this
 *  is a cost as much as a choice, and what was read is corrected by hand anyway. */
const LANGUAGES = ['deu', 'eng']

/** The reading could not be run at all — the script, its core or its data did not
 *  arrive. Its own class, because "nothing was read" is a different fact and sends the
 *  reader somewhere else. */
export class ReadingFailed extends Error {}

type Worker = {
  recognize: (image: Blob) => Promise<{ data: { text: string } }>
  terminate: () => Promise<void>
}

type Reader = {
  createWorker: (
    languages: string[],
    mode: number,
    where: { workerPath: string; corePath: string; langPath: string },
  ) => Promise<Worker>
}

const reader = () => (window as unknown as { Tesseract?: Reader }).Tesseract

let fetching: Promise<Reader> | null = null

/** The script, fetched once. A second photo in the same session waits for nothing. */
function fetched(): Promise<Reader> {
  const already = reader()
  if (already) return Promise.resolve(already)
  if (!fetching) {
    fetching = new Promise<Reader>((arrived, failed) => {
      const script = document.createElement('script')
      script.src = READER
      script.onload = () => {
        const loaded = reader()
        if (loaded) arrived(loaded)
        else failed(new ReadingFailed('the reading could not be run'))
      }
      script.onerror = () => {
        fetching = null
        script.remove()
        failed(new ReadingFailed('the reading could not be run'))
      }
      document.head.append(script)
    })
  }
  return fetching
}

/** The words in an image, as they were recognised.
 *
 *  Throws `ReadingFailed` where the reading never ran. An image holding no text is not
 *  a failure: it comes back as the empty string, which is what the caller tells the
 *  reader about.
 */
export async function read(image: Blob): Promise<string> {
  let engine: Reader
  try {
    engine = await fetched()
  } catch {
    throw new ReadingFailed('the reading could not be run')
  }
  const worker = await engine.createWorker(LANGUAGES, 1, {
    workerPath: WORKER,
    corePath: CORE,
    langPath: DATA,
  })
  try {
    const {
      data: { text },
    } = await worker.recognize(image)
    return text.trim()
  } finally {
    await worker.terminate()
  }
}
