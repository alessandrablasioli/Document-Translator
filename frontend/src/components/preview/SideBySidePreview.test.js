import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import SideBySidePreview from './SideBySidePreview';
import { render } from '../../test-utils';

describe('SideBySidePreview', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('fetches preview and shows original and translated text', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        original_text: 'Hello world',
        translated_text: 'Hola mundo',
      }),
    });

    render(
      <SideBySidePreview
        originalFileId="orig-1"
        translatedFileId="trans-1"
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/preview')
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Hello world')).toBeInTheDocument();
      expect(screen.getByText('Hola mundo')).toBeInTheDocument();
    });

    expect(screen.getByText(/original/i)).toBeInTheDocument();
    expect(screen.getByText(/translated/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('shows error when fetch fails', async () => {
    global.fetch.mockResolvedValue({ ok: false });

    render(
      <SideBySidePreview
        originalFileId="orig-1"
        translatedFileId="trans-1"
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to load preview/i)).toBeInTheDocument();
    });
  });
});
