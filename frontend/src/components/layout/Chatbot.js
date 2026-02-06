import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';
import knowledgeBase from '../../data/knowledgeBase.json';
import { useLanguage } from '../../contexts/LanguageContext';

function Chatbot({ uploadedDocumentText }) {
  const { t, language } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      text: `${t('chatbot.greeting')}\n\n${t('chatbot.greetingSearchHint')}`,
      sender: 'bot'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [suggestionsMenuOpen, setSuggestionsMenuOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const SUGGESTION_KEYS = ['chatbot.suggestion1', 'chatbot.suggestion2', 'chatbot.suggestion3', 'chatbot.suggestion4', 'chatbot.suggestion5', 'chatbot.suggestion6'];

  const handleSuggestionClick = (text) => {
    setInputValue(text);
    inputRef.current?.focus();
  };
  
  // Update greeting when language changes (only if it's the initial greeting)
  useEffect(() => {
    if (messages.length === 1 && messages[0].sender === 'bot') {
      const newGreeting = `${t('chatbot.greeting')}\n\n${t('chatbot.greetingSearchHint')}`;
      if (messages[0].text !== newGreeting) {
        setMessages([{
          text: newGreeting,
          sender: 'bot'
        }]);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, t]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = { text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response (you can integrate with an API later)
    setTimeout(() => {
      const botResponse = getBotResponse(inputValue, t);
      setMessages(prev => [...prev, { text: botResponse, sender: 'bot' }]);
    }, 500);
  };

  const searchInDocument = (query, documentText) => {
    if (!documentText) return null;
    
    const lowerQuery = query.toLowerCase();
    const lowerDoc = documentText.toLowerCase();
    
    // Find all occurrences
    const occurrences = [];
    let index = lowerDoc.indexOf(lowerQuery);
    let count = 0;
    
    while (index !== -1 && count < 5) {
      const start = Math.max(0, index - 100);
      const end = Math.min(documentText.length, index + query.length + 100);
      const snippet = documentText.substring(start, end);
      occurrences.push(snippet.trim());
      index = lowerDoc.indexOf(lowerQuery, index + 1);
      count++;
    }
    
    return occurrences.length > 0 ? occurrences : null;
  };

  const getBotResponse = (userInput, translate) => {
    const input = userInput.toLowerCase().trim();
    const t = translate || (() => '');
    const kb = knowledgeBase[language] || knowledgeBase.en;

    // "What does this page do?" / "What is this page?" → about this page (before generic "what can you do")
    const aboutPagePhrases = [
      'what this page does', 'what the page does', 'what does the page do', 'what does this page do',
      'what is this page', 'what is this app', 'what is this site', 'explain this page', 'explain the page',
      'what this app does', 'what this site does', 'que hace esta pagina', 'qué hace esta página',
      'que hace esta pàgina', 'què fa aquesta pàgina', 'que fait cette page', 'qu\'est-ce que cette page'
    ];
    if (aboutPagePhrases.some((phrase) => input.includes(phrase))) {
      return `${kb.about.title}\n\n${kb.about.description}\n\n${kb.about.purpose}`;
    }

    // "What can you do?" / "Explain what I can do" → single clear answer
    const whatCanYouDoPhrases = ['what can you do', 'what can u do', 'explain what i can do', 'explain me what i can do', 'explain me what you can do', 'what do you do', 'what are you', 'what can the bot do', 'what do you help', 'what are you for', 'qué puedes hacer', 'què pots fer', 'que peux tu faire', 'que puede', 'que pot', 'que peut'];
    if (whatCanYouDoPhrases.some((phrase) => input.includes(phrase)) || /^(what can you|what do you do)\s*[?]?$/i.test(input)) {
      return t('chatbot.whatICanDo') || "I can help you with: understanding what this page does, how to use the translator, supported formats and languages, troubleshooting, and searching inside your uploaded document. What would you like to know?";
    }
    
    // Language-specific keywords for document search
    const docSearchKeywords = {
      en: ['what', 'is', 'in', 'the', 'document', 'does', 'it', 'say', 'find', 'search', 'about', 'contain'],
      es: ['qué', 'está', 'en', 'el', 'documento', 'dice', 'buscar', 'busca', 'sobre', 'contiene'],
      ca: ['què', 'està', 'en', 'el', 'document', 'diu', 'buscar', 'busca', 'sobre', 'conté'],
      fr: ['quoi', 'est', 'dans', 'le', 'document', 'dit', 'chercher', 'recherche', 'sur', 'contient']
    };
    
    const stopWords = docSearchKeywords[language] || docSearchKeywords.en;

    // Summary/preview phrase check (used to enter document branch and to return preview)
    const generalRequestPhrases = [
      'resume of', 'résumé of', 'resume the', 'summary of', 'summarize', 'summarise', 'overview of',
      'resume of the document', 'summary of the document', 'resumen del documento', 'resum del document',
      'tell me about', 'tell me something', 'what\'s in the', 'what is in the', 'whats in the', 'describe the document',
      'content of the', 'last doc', 'last document', 'doc i translated', 'document i translated',
      'what it is about', 'what is it about', 'what is the document about', 'what the document is about',
      'tell me what is the document about', 'tell me what the document is about',
      'make a summary', 'make a summary of', 'give me a summary', 'give me a summary of',
      'parle-moi du', 'dis-moi sur', 'raconte', 'resum del', 'resumen del',
      'conte sobre', 'conte del', 'dime sobre', 'qué hay en', 'què hi ha en', 'quoi dans le'
    ];
    const isGeneralDocumentRequest = generalRequestPhrases.some((phrase) => input.includes(phrase))
      || /^\s*(a\s+)?(summary|resumen|resum|résumé|overview|preview)\s*$/i.test(input.trim());

    // Check if user is asking about the uploaded document
    const docWords = ['document', 'documento', 'fichier', 'doc', 'file', 'archivo', 'fitxer'];
    const contentWords = ['what', 'qué', 'què', 'quoi', 'say', 'dice', 'diu', 'dit', 'find', 'buscar', 'chercher',
      'search', 'busca', 'recherche', 'about', 'sobre', 'sur', 'contain', 'contiene', 'conté', 'contient',
      'summarize', 'resum', 'content', 'contenido', 'contingut', 'contenu', 'topic', 'in the',
      'tell', 'something', 'last', 'translated', 'info', 'information'];
    const mentionsDoc = docWords.some((w) => input.includes(w));
    const asksAboutContent = contentWords.some((w) => input.includes(w));
    const wordCount = input.split(/\s+/).filter(Boolean).length;
    const shortQueryAboutDoc = wordCount <= 3 && mentionsDoc;
    const shortQueryMaybeSearch = wordCount <= 4 && uploadedDocumentText;

    // Trigger document branch: has doc + (content request | short query | summary-style request)
    const isAboutDocument = uploadedDocumentText && (
      (mentionsDoc && asksAboutContent) ||
      shortQueryAboutDoc ||
      shortQueryMaybeSearch ||
      isGeneralDocumentRequest
    );

    // User is asking about the document but no document is uploaded
    if (!uploadedDocumentText && (mentionsDoc || input.includes('document') || input.includes('doc'))) {
      const noDocTexts = {
        en: "No document is uploaded yet. Upload a document (or translate one), then I can search in it, summarize it, or answer questions about it.",
        es: "Aún no has subido ningún documento. Sube un documento (o traduce uno), y podré buscar en él, resumirlo o responder preguntas.",
        ca: "Encara no has pujat cap document. Puja un document (o tradueix-ne un), i podré buscar-hi, resumir-lo o respondre preguntes.",
        fr: "Aucun document n'est téléchargé. Téléchargez un document (ou traduisez-en un), puis je pourrai y rechercher, le résumer ou répondre à vos questions."
      };
      return noDocTexts[language] || noDocTexts.en;
    }

    if (isAboutDocument) {
      // If they want a summary/overview, show preview directly
      if (isGeneralDocumentRequest) {
        const docPreview = uploadedDocumentText.substring(0, 800);
        const previews = {
          en: `Here's a preview/summary of your document:\n\n"${docPreview}${uploadedDocumentText.length > 800 ? '...' : ''}"\n\nYou can ask me to search for specific words or phrases (e.g. "table", "SQL").`,
          es: `Aquí tienes una vista previa/resumen de tu documento:\n\n"${docPreview}${uploadedDocumentText.length > 800 ? '...' : ''}"\n\nPuedes pedirme que busque palabras o frases (ej. "tabla", "SQL").`,
          ca: `Aquí tens una vista prèvia/resum del teu document:\n\n"${docPreview}${uploadedDocumentText.length > 800 ? '...' : ''}"\n\nPots demanar-me que busqui paraules o frases (ex. "taula").`,
          fr: `Voici un aperçu/résumé de votre document:\n\n"${docPreview}${uploadedDocumentText.length > 800 ? '...' : ''}"\n\nVous pouvez me demander de rechercher des mots ou phrases (ex. "table").`
        };
        return previews[language] || previews.en;
      }

      // Extract search term: prefer "information about X" -> X, or "about X" -> X; otherwise filter filler words
      const fillerWords = new Set([
        'searching', 'uploaded', 'document', 'information', 'about', 'your', 'my', 'the', 'in', 'doc', 'file',
        'what', 'find', 'search', 'tell', 'me', 'something', 'last', 'translated', 'documento', 'archivo'
      ]);
      let searchQuery = '';
      const aboutMatch = input.match(/(?:information about|info about|about|sobre|sur)\s+(\w+)/i);
      if (aboutMatch) {
        searchQuery = aboutMatch[1];
      } else {
        const terms = userInput.split(/\s+/).filter(word => {
          const w = word.toLowerCase().replace(/[^\w]/g, '');
          return w.length >= 2 && !fillerWords.has(w) && !stopWords.includes(w);
        });
        searchQuery = terms.length > 0 ? terms.join(' ') : userInput.trim();
      }
      if (searchQuery.length > 100) searchQuery = searchQuery.substring(0, 100);

      if (searchQuery) {
        const results = searchInDocument(searchQuery, uploadedDocumentText);
        const responses = {
          en: {
            found: (query, count) => `I found "${query}" in your document:\n\n`,
            occurrences: (count) => `(Found ${count} total occurrences)`,
            notFound: (query) => `I couldn't find "${query}" in your document. Try a different word or ask for a summary.`
          },
          es: {
            found: (query, count) => `Encontré "${query}" en tu documento:\n\n`,
            occurrences: (count) => `(Encontradas ${count} ocurrencias en total)`,
            notFound: (query) => `No encontré "${query}" en tu documento. Prueba otra palabra o pide un resumen.`
          },
          ca: {
            found: (query, count) => `He trobat "${query}" al teu document:\n\n`,
            occurrences: (count) => `(Trobades ${count} ocurrències en total)`,
            notFound: (query) => `No he trobat "${query}" al teu document. Prova una altra paraula o demana un resum.`
          },
          fr: {
            found: (query, count) => `J'ai trouvé "${query}" dans votre document:\n\n`,
            occurrences: (count) => `(${count} occurrences trouvées au total)`,
            notFound: (query) => `Je n'ai pas trouvé "${query}" dans votre document. Essayez un autre mot ou demandez un résumé.`
          }
        };
        const resp = responses[language] || responses.en;
        if (results && results.length > 0) {
          let response = resp.found(searchQuery, results.length);
          results.slice(0, 3).forEach((snippet, idx) => {
            response += `${idx + 1}. ...${snippet}...\n\n`;
          });
          if (results.length > 3) {
            response += resp.occurrences(results.length);
          }
          return response;
        } else {
          return resp.notFound(searchQuery);
        }
      } else {
        const docPreview = uploadedDocumentText.substring(0, 600);
        const previews = {
          en: `Here's a preview of your document:\n\n"${docPreview}${uploadedDocumentText.length > 600 ? '...' : ''}"\n\nAsk me to search for a word (e.g. "table") or "tell me about the document".`,
          es: `Aquí tienes una vista previa de tu documento:\n\n"${docPreview}${uploadedDocumentText.length > 600 ? '...' : ''}"\n\nPídeme buscar una palabra (ej. "tabla") o "cuéntame del documento".`,
          ca: `Aquí tens una vista prèvia del teu document:\n\n"${docPreview}${uploadedDocumentText.length > 600 ? '...' : ''}"\n\nDemana'm buscar una paraula (ex. "taula") o "explica'm el document".`,
          fr: `Voici un aperçu de votre document:\n\n"${docPreview}${uploadedDocumentText.length > 600 ? '...' : ''}"\n\nDemandez-moi de rechercher un mot (ex. "table") ou "parlez-moi du document".`
        };
        return previews[language] || previews.en;
      }
    }

    // More "about this page" variations (longer phrases)
    if (input.includes('que hace') || input.includes('qué hace') || input.includes('entender que hace') || input.includes('entender qué hace')
        || input.includes('que es') || input.includes('qué es') || input.includes('que es esto') || input.includes('qué es esto')
        || input.includes('que es la pagina') || input.includes('qué es la página') || input.includes('sobre esta pagina') || input.includes('sobre esta página')
        || input.includes('what is this') || input.includes('what is the page') || input.includes('about this page') || input.includes('what does this do')
        || input.includes('què és això') || input.includes('què és la pàgina') || input.includes('sobre aquesta pàgina') || input.includes('entendre què fa')
        || input.includes('qu\'est-ce que') || input.includes('qu\'est-ce que cette page') || input.includes('à propos de cette page') || input.includes('comprendre ce que fait')) {
      return `${kb.about.title}\n\n${kb.about.description}\n\n${kb.about.purpose}`;
    }

    if (input.includes('format') || input.includes('file type') || input.includes('supported format')
        || input.includes('formato') || input.includes('tipo de archivo') || input.includes('formatos soportados')
        || input.includes('format') || input.includes('tipus de fitxer') || input.includes('formats suportats')
        || input.includes('format') || input.includes('type de fichier') || input.includes('formats supportés')) {
      const formats = kb.features.supportedFormats.join('\n');
      const formatTexts = {
        en: `Supported file formats:\n\n${formats}\n\nMaximum file size: ${kb.features.maxFileSize}`,
        es: `Formatos de archivo soportados:\n\n${formats}\n\nTamaño máximo de archivo: ${kb.features.maxFileSize}`,
        ca: `Formats de fitxer suportats:\n\n${formats}\n\nMida màxima del fitxer: ${kb.features.maxFileSize}`,
        fr: `Formats de fichier supportés:\n\n${formats}\n\nTaille maximale du fichier: ${kb.features.maxFileSize}`
      };
      return formatTexts[language] || formatTexts.en;
    }

    if (input.includes('language') || input.includes('translate to')
        || input.includes('idioma') || input.includes('traducir a')
        || input.includes('idioma') || input.includes('traduir a')
        || input.includes('langue') || input.includes('traduire en')) {
      const languages = kb.features.supportedLanguages.join(', ');
      const langTexts = {
        en: `Supported languages:\n\n${languages}\n\nSelect your target language from the dropdown menu.`,
        es: `Idiomas soportados:\n\n${languages}\n\nSelecciona tu idioma de destino del menú desplegable.`,
        ca: `Idiomes suportats:\n\n${languages}\n\nSelecciona el teu idioma de destinació del menú desplegable.`,
        fr: `Langues supportées:\n\n${languages}\n\nSélectionnez votre langue cible dans le menu déroulant.`
      };
      return langTexts[language] || langTexts.en;
    }

    if (input.includes('how to') || input.includes('how do i') || input.includes('steps')
        || input.includes('cómo') || input.includes('cómo se') || input.includes('pasos')
        || input.includes('com') || input.includes('com es') || input.includes('passos')
        || input.includes('comment') || input.includes('comment faire') || input.includes('étapes')) {
      const steps = Object.values(kb.howToUse).join('\n\n');
      const howToTexts = {
        en: `How to use:\n\n${steps}`,
        es: `Cómo usar:\n\n${steps}`,
        ca: `Com usar:\n\n${steps}`,
        fr: `Comment utiliser:\n\n${steps}`
      };
      return howToTexts[language] || howToTexts.en;
    }

    if (input.includes('error') || input.includes('problem') || input.includes('issue') || input.includes('not working') || input.includes('troubleshoot')
        || input.includes('error') || input.includes('problema') || input.includes('problema') || input.includes('no funciona')
        || input.includes('error') || input.includes('problema') || input.includes('problema') || input.includes('no funciona')
        || input.includes('erreur') || input.includes('problème') || input.includes('ne fonctionne pas')) {
      const troubleshooting = Object.entries(kb.troubleshooting)
        .map(([key, value]) => `${key.replace(/([A-Z])/g, ' $1').trim()}: ${value}`)
        .join('\n\n');
      const troubleshootTexts = {
        en: `Troubleshooting:\n\n${troubleshooting}`,
        es: `Solución de problemas:\n\n${troubleshooting}`,
        ca: `Resolució de problemes:\n\n${troubleshooting}`,
        fr: `Dépannage:\n\n${troubleshooting}`
      };
      return troubleshootTexts[language] || troubleshootTexts.en;
    }

    if (input.includes('feature') || input.includes('what can') || input.includes('capabilities')
        || input.includes('característica') || input.includes('qué puede') || input.includes('capacidades')
        || input.includes('característica') || input.includes('què pot') || input.includes('capacitats')
        || input.includes('fonctionnalité') || input.includes('que peut') || input.includes('capacités')) {
      const featureTexts = {
        en: `Features:\n\n• Supports ${kb.features.supportedFormats.length} file formats\n• ${kb.features.supportedLanguages.length}+ languages\n• ${kb.features.translationEngine}\n• Maximum file size: ${kb.features.maxFileSize}`,
        es: `Características:\n\n• Soporta ${kb.features.supportedFormats.length} formatos de archivo\n• ${kb.features.supportedLanguages.length}+ idiomas\n• ${kb.features.translationEngine}\n• Tamaño máximo de archivo: ${kb.features.maxFileSize}`,
        ca: `Característiques:\n\n• Suporta ${kb.features.supportedFormats.length} formats de fitxer\n• ${kb.features.supportedLanguages.length}+ idiomes\n• ${kb.features.translationEngine}\n• Mida màxima del fitxer: ${kb.features.maxFileSize}`,
        fr: `Fonctionnalités:\n\n• Prend en charge ${kb.features.supportedFormats.length} formats de fichier\n• ${kb.features.supportedLanguages.length}+ langues\n• ${kb.features.translationEngine}\n• Taille maximale du fichier: ${kb.features.maxFileSize}`
      };
      return featureTexts[language] || featureTexts.en;
    }

    // Check for general questions about understanding the page
    if (input.includes('entender') || input.includes('comprendre') || input.includes('understand')
        || input.includes('saber') || input.includes('saber que') || input.includes('savoir')) {
      // If asking about understanding what the page does
      if (input.includes('hace') || input.includes('fa') || input.includes('fait') || input.includes('does')
          || input.includes('es') || input.includes('és') || input.includes('est') || input.includes('is')) {
        return `${kb.about.title}\n\n${kb.about.description}\n\n${kb.about.purpose}`;
      }
    }

    // Default response: same concise "what I can do" message
    return t('chatbot.whatICanDo') || "I can help you with: understanding what this page does, how to use the translator, supported formats and languages, troubleshooting, and searching inside your uploaded document. What would you like to know?";
  };

  return (
    <>
      {!isOpen && (
        <button 
          className="chatbot-toggle"
          onClick={() => setIsOpen(true)}
          aria-label="Open chatbot"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
          </svg>
        </button>
      )}

      {isOpen && (
        <div className="chatbot-container">
          <div className="chatbot-header">
            <div className="chatbot-header-content">
              <h3>{t('chatbot.title')}</h3>
              <p>{t('chatbot.subtitle')}</p>
            </div>
            <button 
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chatbot"
            >
              ×
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.sender}`}>
                <div className="message-content">
                  {message.text.split('\n').map((line, i) => (
                    <React.Fragment key={i}>
                      {line}
                      {i < message.text.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-suggestions-menu">
            {suggestionsMenuOpen ? (
              <>
                <div className="chatbot-suggestions-menu-header">
                  <span className="chatbot-suggestions-menu-title">{t('chatbot.suggestionsTitle')}</span>
                  <button
                    type="button"
                    className="chatbot-suggestions-menu-close"
                    onClick={() => setSuggestionsMenuOpen(false)}
                    aria-label="Close suggestions"
                  >
                    ×
                  </button>
                </div>
                <ul className="chatbot-suggestions-list">
                  {SUGGESTION_KEYS.map((key) => (
                    <li key={key}>
                      <button
                        type="button"
                        className="chatbot-suggestion-item"
                        onClick={() => handleSuggestionClick(t(key))}
                      >
                        {t(key)}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <button
                type="button"
                className="chatbot-suggestions-menu-toggle"
                onClick={() => setSuggestionsMenuOpen(true)}
              >
                <span>{t('chatbot.suggestionsMenuLabel')}</span>
                <svg className="chatbot-suggestions-chevron" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
          </div>

          <form className="chatbot-input-form" onSubmit={handleSend}>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={t('chatbot.placeholder')}
              className="chatbot-input"
            />
            <button type="submit" className="chatbot-send">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default Chatbot;
