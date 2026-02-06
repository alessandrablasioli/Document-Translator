import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { render } from './test-utils';

describe('App user flow', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('renders app title and upload area when no file is uploaded', () => {
    render(<App />);
    expect(screen.getByRole('button', { name: /the stark future of translation/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /the stark future of translation/i }));
    expect(screen.getByRole('heading', { name: /upload document/i })).toBeInTheDocument();
  });

  it('full user flow: upload file -> select language -> translate -> see result (mocked API)', async () => {
    const mockFileId = 'test-file-id-123';
    const mockTranslatedId = 'translated-id-456';

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ file_id: mockFileId, filename: 'doc.txt', file_type: '.txt' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ text: 'Hello world' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          file_id: mockTranslatedId,
          file_type: '.txt',
          status: 'completed',
          message: 'Translation completed successfully',
        }),
      });

    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /the stark future of translation/i }));

    // 1. Upload: select a file
    const file = new File(['hello'], 'doc.txt', { type: 'text/plain' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/upload'),
        expect.objectContaining({ method: 'POST' })
      );
    });

    // 2. After upload we see the translation form
    await waitFor(() => {
      expect(screen.getByText(/file uploaded/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /translate document/i })).toBeInTheDocument();
    });

    // 3. Click translate
    fireEvent.click(screen.getByRole('button', { name: /translate document/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/translate'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining(mockFileId),
        })
      );
    });

    // 4. See completion and download option (download is a link, not a button)
    await waitFor(() => {
      expect(screen.getByText(/translation complete/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /download translated document/i })).toBeInTheDocument();
    });
  });

  it('reset clears state and shows upload again', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ file_id: 'id', filename: 'f.txt', file_type: '.txt' }),
    });

    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /the stark future of translation/i }));
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [new File(['x'], 'f.txt', { type: 'text/plain' })] } });

    await waitFor(() => expect(screen.getByRole('button', { name: /upload new file/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /upload new file/i }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /upload document/i })).toBeInTheDocument();
      expect(screen.queryByText(/file uploaded/i)).not.toBeInTheDocument();
    });
  });

  it('batch flow: multiple files upload -> Translate All -> batch results', async () => {
    const file1 = new File(['a'], 'a.txt', { type: 'text/plain' });
    const file2 = new File(['b'], 'b.txt', { type: 'text/plain' });
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ file_id: 'id1', filename: 'a.txt' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ file_id: 'id2', filename: 'b.txt' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          results: [
            { original_file_id: 'id1', translated_file_id: 't1', status: 'completed' },
            { original_file_id: 'id2', translated_file_id: 't2', status: 'completed' },
          ],
          total: 2,
        }),
      });

    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /the stark future of translation/i }));
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file1, file2] } });

    await waitFor(() => {
      expect(screen.getByText(/2 files/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /translate all/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /translate all/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/translate-batch'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('id1'),
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/translation completed/i)).toBeInTheDocument();
      expect(screen.getByText('a.txt')).toBeInTheDocument();
      expect(screen.getByText('b.txt')).toBeInTheDocument();
    });
  });
});
