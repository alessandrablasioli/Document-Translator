import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import TranslationHistory from './TranslationHistory';
import { render } from '../../test-utils';

describe('TranslationHistory', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('fetches and shows history list', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        history: [
          {
            id: 'h1',
            original_file_id: 'o1',
            translated_file_id: 't1',
            filename: 'doc.txt',
            target_language: 'Spanish',
            timestamp: Math.floor(Date.now() / 1000),
          },
        ],
      }),
    });

    const mockOnPreview = jest.fn();
    render(<TranslationHistory onPreview={mockOnPreview} onClose={() => {}} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/history')
      );
    });

    await waitFor(() => {
      expect(screen.getByText('doc.txt')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /preview/i }));
    expect(mockOnPreview).toHaveBeenCalledWith('o1', 't1');
  });

  it('shows empty state when no history', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ history: [] }),
    });

    render(<TranslationHistory onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/no translations yet/i)).toBeInTheDocument();
    });
  });

  it('shows error when fetch fails', async () => {
    global.fetch.mockResolvedValue({ ok: false });

    render(<TranslationHistory onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load history/i)).toBeInTheDocument();
    });
  });
});
