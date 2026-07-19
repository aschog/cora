# Feature Plan: Document Ingestion

Roadmap item 2 (`docs/plans/webapp-overview.md` §10). Branch: `feature/document-ingestion`.

## Requirements

From the architecture plan (§4 Ingestion, §6 ingestion flow & error philosophy):

- Given raw bytes plus a filename, produce clean text and split it into ordered, overlapping chunks, each carrying provenance metadata (source name, chunk index, character offset).
- Supported formats: txt, md, pdf — decided by filename extension.
- Reject unsupported file types, oversized files, and documents that are empty after text extraction; reject unreadable (corrupt) files. Every rejection is a typed error with a user-presentable message — no stack traces, no third-party exceptions escaping.
- Pure core logic: no framework imports, nothing external except the confined PDF library (pypdf). Runs entirely in the unit tier — no network, no model downloads, no UI.

**Acceptance criteria:** txt/md/pdf bytes + filename → ordered chunks with provenance suitable for later embedding/storage; unsupported/oversized/empty/corrupt inputs raise typed errors with user-presentable messages; all unit-tier gates (format, lint, types, tests) green.

## Design (architecture level)

**Components touched.** One new core component, Ingestion, with one public entry point: bytes + filename in, ordered chunks out. Internally three stages matching the runtime flow: *validate → extract → chunk*. This feature also creates the project-wide **exception hierarchy** that later features (knowledge base, chat, plugins) extend.

**Chunks as value objects.** A chunk is an immutable value carrying its text plus provenance (source name, zero-based index, character offset into the cleaned source text). Value semantics (equality by content) make chunker tests trivial assertions and make the later knowledge-base dedupe and citation rendering straightforward — the pattern already reserved in overview §5.

**Loaders: simple dispatch, not Strategy classes.** Text extraction is a mapping from file extension to a small pure function (bytes → text). Three formats, two of which (txt, md) are the same decode, do not justify a Strategy class hierarchy with an abstract loader interface — *simplicity first; every abstraction must earn its place*. The dispatch table **is** the extension seam: supporting a new format later means adding one function and one table entry, and the table doubles as the single source of truth for the supported-type allow-list used in validation and in error messages. If loaders ever grow per-format configuration or state, promoting the table to Strategy objects is a mechanical refactor done on tested ground.

**pypdf quarantine.** pypdf is imported in exactly one module — the PDF loader — mirroring the one-adapter-per-volatile-dependency rule (overview §2, §5) even though it lives inside the core: pypdf is pure Python with zero dependencies and fully deterministic, so it is unit-tier safe, but its API churn must not leak. The loader is the translation boundary: it catches pypdf's base exception (`PyPdfError`) and re-raises the project's typed unreadable-file error; no pypdf type crosses the module boundary in either direction. Pages are joined in document order with a paragraph break between them so the chunker's separator ladder naturally respects page edges; blank/image-only pages (which extract to empty strings) contribute nothing. OCR is out of scope.

**Chunker: hand-written recursive character splitter.** Pure Python, no library — LangChain (and its splitters) stays confined to the future LLM adapter per the dependency rule. Separator ladder: paragraph (`\n\n`) → line (`\n`) → word (space) → hard character fallback, so splits land at the most semantic boundary available within the size budget. Chunk size and overlap are **parameters with defaults** (~1000 chars, ~150–200 overlap — sized to the all-MiniLM-L6-v2 256-token truncation window per research), so the knowledge-base feature can tune them without touching ingestion. Bad parameter values (non-positive size, overlap ≥ size) are programmer errors, not user errors — they raise a plain built-in error rather than joining the user-facing hierarchy.

**Error hierarchy (created here).** One small base error for the whole application, whose contract is: every instance carries a user-presentable message. Ingestion contributes the first four leaf categories: unsupported file type, file too large, empty document, unreadable file. Validation order in the entry point: type and size checks on the raw bytes (cheap, before any parsing), extraction, then the emptiness check on the extracted text (format-agnostic — a whitespace-only txt and an image-only PDF fail identically). Later features add sibling categories (provider errors, plugin errors) under the same base, giving the UI shell a single catch point.

**How this feeds the knowledge base (roadmap item 3).** The KB facade will call the ingestion entry point and pass the resulting chunk values to the embedder and retriever ports; provenance metadata travels with each chunk into the vector store and comes back as citation data in the chat flow. Ordered indices and character offsets give the KB stable identifiers for dedupe and give citations a position to point at. Ingestion needs no knowledge of any port — the dependency arrow points from KB to ingestion only.

## TDD checklist

Every item is one red → green → refactor cycle; commit each green step (`docs/workflow.md` Phase 2).

**Errors (the hierarchy is born here)**
- [ ] Write a test that shows the application base error exposes a user-presentable message
- [ ] Write a test that shows the four ingestion errors (unsupported type, too large, empty document, unreadable file) are subtypes of the base error and their messages name the offending file

**Chunk value object**
- [ ] Write a test that shows a chunk is an immutable value: equal by content (text + provenance), mutation attempts fail

**Chunker (pure, bottom of the stack)**
- [ ] Write a test that shows chunking empty text yields no chunks
- [ ] Write a test that shows text shorter than the chunk size yields exactly one chunk containing the full text, with source name, index 0, offset 0
- [ ] Write a test that shows invalid parameters (non-positive chunk size, overlap ≥ chunk size) are rejected as programmer errors
- [ ] Write a test that shows long text splits into multiple chunks, each within the size budget
- [ ] Write a test that shows a paragraph break near the size limit becomes the split point (no mid-sentence cut when `\n\n` is available)
- [ ] Write a test that shows text without paragraph breaks splits at line breaks, and without those at word boundaries
- [ ] Write a test that shows one unbroken run of characters longer than the chunk size is hard-split rather than looping or overflowing
- [ ] Write a test that shows consecutive chunks overlap by the configured amount (tail of chunk *n* reappears at the head of chunk *n+1*)
- [ ] Write a test that shows chunk indices are consecutive from zero and each chunk's offset locates its text in the source

**Text cleaning**
- [ ] Write a test that shows extracted text is normalized: CRLF becomes LF, surrounding whitespace is trimmed, runs of 3+ blank lines collapse to one paragraph break

**Loaders — txt / md**
- [ ] Write a test that shows UTF-8 txt bytes decode to their text
- [ ] Write a test that shows undecodable bytes under a `.txt` name raise the unreadable-file error
- [ ] Write a test that shows md bytes load like txt, markup preserved verbatim

**Loaders — pdf** (`uv add pypdf` — pinned `>=6.14,<7` — as part of the first red step below)
- [ ] Write the in-test PDF fixture helper (pypdf writer API, no checked-in binaries) with a test that shows a generated single-page PDF round-trips its sentence through the PDF loader
- [ ] Write a test that shows a multi-page PDF yields pages in order, joined by a paragraph break
- [ ] Write a test that shows blank/image-only pages contribute nothing and raise nothing
- [ ] Write a test that shows corrupt PDF bytes raise the unreadable-file error (pypdf's exception never escapes)

**Validation + entry point (top of the stack)**
- [ ] Write a test that shows an unsupported extension raises the unsupported-type error whose message lists the supported formats
- [ ] Write a test that shows extension matching is case-insensitive and a filename without an extension is rejected as unsupported
- [ ] Write a test that shows bytes over the size limit (a parameter with a default) raise the too-large error before any parsing
- [ ] Write a test that shows a document that is empty after extraction (whitespace-only txt, image-only pdf) raises the empty-document error
- [ ] Write a test that shows the entry point end-to-end: txt bytes + filename yield ordered chunks whose source name is the filename
- [ ] Write a test that shows the entry point end-to-end for a fixture-generated PDF, provenance intact

## Trade-offs considered / rejected alternatives

- **Dispatch table vs. Strategy classes for loaders** — rejected Strategy: three formats, stateless pure functions, no per-format configuration; a class hierarchy adds ceremony without variance to manage. Promotion path exists if loaders grow state.
- **LangChain text splitters** — rejected: violates the confinement rule (LangChain = LLM adapter only) and drags a heavy dependency into the core for ~40 lines of pure logic we want to unit-test directly.
- **pdfplumber / PyMuPDF instead of pypdf** — rejected per research: pypdf is pure Python, zero-dependency, BSD-licensed, and its extraction quality suffices for text-based PDFs; PyMuPDF's AGPL license and native builds are unjustified. OCR for scanned PDFs is explicitly out of scope.
- **Page-number provenance for PDFs** — deferred: source + index + char offset satisfies the plan's "(source, position)" and keeps provenance format-agnostic; page numbers would leak format-specific metadata into the chunk contract. Revisit if citation UX demands it.
- **Checked-in binary PDF fixtures** — rejected: generated at test time via pypdf's writer API; parameterizable, reviewable, no binary blobs in the repo.
- **MIME sniffing instead of extension dispatch** — rejected: extension checking is deterministic, dependency-free, and matches the UI upload flow where filenames are always present; content sniffing adds complexity without a real threat model here (a mislabeled file fails loudly at extraction with a typed error anyway).
- **Chunk size in tokens** — rejected: token-accurate sizing needs a tokenizer (a model download, banned from the unit tier); character-based sizing with embedder-informed defaults is deterministic and adjustable via parameters.
