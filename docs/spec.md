### Core requirements

- webapp for chatting with your own documents
- only core features as simple as possible
- extensible with plugins
- frontend with Streamlit, should be replaceable
- backend with python

1. **RAG Implementation:**
   - Create a knowledge base relevant to your domain
   - Implement standard document retrieval with embeddings
   - Use chunking strategies and similarity search

2. **Tool Calling:**
   - Implement at least 3 different tool calls
   - Functions should be relevant to your domain
   - Examples: data analysis, calculations, API integrations

3. **Domain Specialisation:**
   - Choose a specific domain or use case
   - Create a focused knowledge base
   - Implement domain-specific prompts and responses
   - Add relevant security measures for your domain

4. **Technical Implementation:**
   - Use LangChain with OpenRouter (OpenAI-compatible SDK) for LLM integration
   - Implement proper error handling
   - Include user input validation

5. **User Interface:**
   - Create an intuitive interface using Streamlit or Next.js
   - Show relevant context and sources
   - Display tool call results
   - Include progress indicators for long operations

### Medium requirements

The optional tasks chosen for the bonus (two medium). Each plugs into an existing
seam so it stays a small, isolated addition.

1. **Visualisation of tool-call results:** *(done)*
   - Render each tool call's result under the answer in the UI

2. **Prompt-injection protection:** *(planned)*
   - Detect injection / jailbreak patterns as a validation rule in the pipeline
   - Add the guard by adding a rule, not by editing a component

### Hard requirements

The optional task chosen for the bonus (one hard).

1. **Hybrid search:** *(planned)*
   - Add a sparse (BM25) retriever behind the existing `Retriever` port
   - Fuse sparse and dense rankings with the existing reciprocal rank fusion
