import React from 'react';
import { render } from '@testing-library/react';
import { LanguageProvider } from './contexts/LanguageContext';

/**
 * Wrap component with LanguageProvider so useLanguage() works in tests.
 */
function renderWithLanguage(ui, options = {}) {
  function Wrapper({ children }) {
    return <LanguageProvider>{children}</LanguageProvider>;
  }
  return render(ui, { wrapper: Wrapper, ...options });
}

export { renderWithLanguage as render };
