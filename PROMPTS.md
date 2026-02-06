# Prompts I Used to Build the App

Log of the **prompts I (the user) wrote** to the AI assistant while building the Document Translator. These are the instructions I gave to build and refine the application.

---

## Fundamentals (project brief)

Core instructions that define what the app is and what it must satisfy:

**The challenge**
- Build the best possible AI-powered document translation tool.
- **Input:** A file + a target language  
- **Output:** The same file, translated

**Minimum viable product**
- Web interface that:
  1. Accepts PDF uploads
  2. Translates the content using an **OpenAI Agents SDK** (`openai-agents`)
  3. Outputs a translated PDF

**Hard requirements**

| Requirement      | Details                                           |
|------------------|---------------------------------------------------|
| **Backend**      | Python + FastAPI                                  |
| **AI**           | OpenAI Agents SDK (`openai-agents`)               |
| **Frontend**     | Your choice                                       |
| **Delivery**     | Git repo with `docker compose up` that works      |
| **PROMPTS.md**   | Log of all AI prompts used during development     |
| **README.md**    | Explain agent architecture and design choices      |
| **RETROSPECTIVE.md** | "If you had to start over, what would you do differently?" |

**API key:** Stored in `.env`, never committed; optional at app init for local dev. Budget-conscious use of models.

**Branding:** Stark (from [starkfuture.com](https://starkfuture.com/es-ES)) — logos, fonts, and visual identity.

Everything beyond the MVP (more formats, batch, history, preview, chatbot, MCP, etc.) was added on top of these fundamentals.

---

### Initial setup
```
Please read the md document and create a todo plan. make sure to create all the necessary files satisfying the Hard Requirements table
```

---

### PROMPTS.md
```
**PROMPTS.md**       | Log of **all** AI prompts used during development   are you doing it?
```

---

### Languages
```
can you add the support to english, catalan, spanish and french
```

---

### PROMPTS file clarity
```
can you adjust the prompt md file making clear what are the prompt im using in the chat and nothing else?
```

---

### Update PROMPTS every time
```
okay update it every time i write something here
```

---

### API key privacy
```
I want for sure that the API key stays private in an .env file
```

---

### Multi-format support
```
is it supporting only pdf? i would like a method that based on the type of the file ( can be pdf, md, json, xml, docx ecc) calls a dedicated funcrtion to load the file
```

```
structure the code as it is for pdf (so in another file the service for every kind of document, put it in a subfolder od backend)
```

---

### DOCX implementation
```
@docx_service.py (45-52) why are you not implementing it?
```

---

### API key optional at init
```
can you ignore the fact that there is not the open api key still?
```

---

### Stark branding
```
okay let's do the graphics Branded for **Stark** (find some branding online) https://starkfuture.com/es-ES
```

```
nsert those logos and use the same font as this page https://starkfuture.com/es-ES
```

---

### Chatbot
```
add this up and the logo.svg down. add a pop up down on the left where there is a window that opens a chatbot and is like: do you need help? and the chatbot can help you understand better the doc or if you have any issue
```

```
no make it bottom right. buoild a knowlege base as a json where you put basic information like what is this page used for and then use it to answer in the help chatbot. then if the user asks something about the document itself make it possible to search into the document
```

---

### Language selector (UI language)
```
make possible to change the language of ALL the page from a little window up right
```

---

### Chatbot respond in same language
```
the first message in the chat is in the correct language eg. spanish, if i write in spanish then answers in English... it should answer in the same language is the page in that moment
```

---

### OpenAI Agents SDK and features
```
prioritize Migrate to OpenAI Agents SDK (critical fix) but do all
```

---

### Chatbot question detection
```
the chatbot is not working fine - it's not detecting questions properly, especially Spanish questions like "que hace este traductor?" and "quiero entender que hace esta pagina"
```

---

### PowerPoint support
```
maybe i woul like to add other formats like powerpoint for example
```

---

### Code structure (document processors)
```
structure the code as it is for pdf (so in another file the service for every kind of document, put it in a subfolder od backend)
```

---

### Batch, preview, history, tests
```
@EXTENSIONS_ANALYSIS.md:239-244 do it add also tests etc
```
(Referring to Batch Processing, Side-by-Side Preview, Real-Time Progress, Translation History + tests.)

---

### Refactor to OpenAI Agents SDK
```
okay lets do it, refactor to openAI agents sdk
```
(Refactored translation path to use `openai-agents`: Agent + FunctionTools + Runner in `sdk_translation_workflow.py`; orchestrator delegates to it; same API response shape.)

