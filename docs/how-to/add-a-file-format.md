# Add a file format

Which formats can be uploaded is a registry entry, not a branch inside ingestion.

1. **Write the loader.** In `src/cora/adapters/loaders.py`, a loader takes the bytes and
   the filename and returns text. Raise `UnreadableFileError(filename)` when the bytes
   cannot be read — that is the message the user sees:

   ```python
   def load_docx(data: bytes, filename: str) -> str:
       try:
           return "\n\n".join(paragraph.text for paragraph in Document(BytesIO(data)).paragraphs)
       except PackageNotFoundError as exc:
           raise UnreadableFileError(filename) from exc
   ```

2. **Register the extension.** Add it to `LOADERS` in the same file, lowercase and with
   its dot:

   ```python
   LOADERS: Loaders = {".txt": load_txt, ".md": load_txt, ".pdf": load_pdf, ".docx": load_docx}
   ```

   Ingestion reads the registry: an extension it does not hold is refused with
   `UnsupportedFileTypeError`, which names the ones it does.

3. **Add the dependency** it needs — `uv add python-docx` — never by editing the
   lockfile.

4. **Widen the two uploaders.** Each frontend states the extensions it offers, so a
   format registered but not offered cannot be picked: `st.file_uploader(…, type=…)` in
   `frontends/streamlit/src/cora/frontends/streamlit/chat.py`, and the `accept`
   attribute in `frontends/react/ui/src/components/DocumentRail.tsx`.
