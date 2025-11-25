import React, { useState, useRef } from 'react';
import { Box, Fab, Drawer, IconButton, TextField, Button, Divider, Typography, CircularProgress, Stack } from '@mui/material';
import { Chat as ChatIcon, Send as SendIcon, Close as CloseIcon, Link as LinkIcon } from '@mui/icons-material';
import { apiService } from '../services/api';

type ChatMessage = {
  role: 'user' | 'assistant';
  text: string;
  citations?: Array<{ title: string; url: string }>;
};

const ChatbotWidget: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Hola 👋 ¿En qué te ayudo? Puedes pedirme: buscar, resumir, filtrar por fecha (YYYY-MM-DD a YYYY-MM-DD) o consultar tu plan.' },
  ]);
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const quickPrompts = [
    { label: 'La República hoy', value: 'la república hoy' },
    { label: 'Resumen selección peruana', value: 'resumen selección peruana esta semana' },
    { label: 'Mi plan actual', value: 'mi plan' },
    { label: 'RPP 2025 completo', value: 'rpp 2025-01-01 a 2025-12-31' },
  ];

  const send = async () => {
    const msg = input.trim();
    if (!msg) return;
    setMessages((m) => [...m, { role: 'user', text: msg }]);
    setInput('');
    setLoading(true);
    try {
      // detectar rango de fechas en el mensaje: "2025-01-01 a 2025-12-31"
      let date_from: string | undefined;
      let date_to: string | undefined;
      const m = msg.match(/(20\d{2}-\d{2}-\d{2})\s*(?:a|hasta|to)\s*(20\d{2}-\d{2}-\d{2})/i);
      if (m) { date_from = m[1]; date_to = m[2]; }
      const resp = await apiService.chat({ message: msg, date_from, date_to, limit: 10 });
      const replyText: string = resp.reply || 'Listo.';
      const citations: Array<{ title: string; url: string }> = resp.citations || [];
      setMessages((m) => [...m, { role: 'assistant', text: replyText, citations }]);
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.message || 'Error al consultar el chatbot.';
      setMessages((m) => [...m, { role: 'assistant', text: `⚠️ ${errMsg}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading) send();
    }
  };

  return (
    <>
      {!open && (
      <Fab color="primary" onClick={() => setOpen(true)} sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1300 }}>
        <ChatIcon />
      </Fab>
      )}

      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        ModalProps={{ keepMounted: true }}
        PaperProps={{
          sx: {
            width: { xs: '92%', sm: 340, md: 360 },
            maxWidth: 360,
            height: { xs: '94vh', sm: '85vh' },
            mt: { xs: '3vh', sm: '7vh' },
            mb: { xs: '3vh', sm: '3vh' },
            mr: { sm: 3 },
            borderRadius: { xs: 2, sm: 3 },
            border: '1px solid',
            borderColor: 'rgba(15,23,42,0.08)',
            boxShadow: '0 30px 60px rgba(15,23,42,0.15)',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        <Box
          sx={{
            p: 2.25,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            bgcolor: 'linear-gradient(135deg, #0284c7, #0ea5e9)',
            color: 'primary.contrastText'
          }}
        >
          <Box>
            <Typography variant="subtitle2" sx={{ opacity: 0.9, textTransform: 'uppercase', letterSpacing: 1 }}>Asistente</Typography>
            <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.2 }}>¿En qué te ayudo hoy?</Typography>
          </Box>
          <IconButton onClick={() => setOpen(false)} sx={{ color: 'inherit' }}><CloseIcon /></IconButton>
        </Box>
        <Divider />
        <Box ref={listRef} sx={{ p: 2, flex: 1, overflowY: 'auto', bgcolor: '#f8fafc' }}>
          <Box sx={{ mb: 1.8 }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 0.4 }}>Sugerencias rápidas</Typography>
            <Stack spacing={1} sx={{ mt: 1.2 }}>
              {quickPrompts.map((qp) => (
                <Button
                  key={qp.value}
                  variant="outlined"
                  onClick={() => setInput(qp.value)}
                  sx={{
                    justifyContent: 'flex-start',
                    borderRadius: 3,
                    textTransform: 'none',
                    borderColor: 'rgba(2,132,199,0.2)',
                    color: 'text.primary',
                    backgroundColor: 'white',
                    fontWeight: 600,
                    '&:hover': {
                      borderColor: 'primary.main',
                      backgroundColor: 'rgba(14,165,233,0.08)'
                    }
                  }}
                >
                  {qp.label}
                </Button>
              ))}
            </Stack>
          </Box>
          <Box
            sx={{
              mb: 2,
              p: 1.5,
              bgcolor: 'white',
              borderRadius: 3,
              border: '1px solid rgba(15,23,42,0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: 1.2
            }}
          >
            <Box
              sx={{
                width: 42,
                height: 42,
                borderRadius: '50%',
                bgcolor: 'rgba(14,165,233,0.15)',
                display: 'grid',
                placeItems: 'center',
                fontWeight: 700,
                color: '#0284c7'
              }}
            >
              AI
            </Box>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Asistente virtual</Typography>
              <Typography variant="body2" color="text.secondary">
                Pregúntame por noticias, resúmenes, filtros por fecha o tu plan activo.
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.1 }}>
            {messages.map((m, i) => {
              const isUser = m.role === 'user';
              return (
                <Box key={i} sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                  <Box sx={{
                    maxWidth: '85%',
                    bgcolor: isUser ? 'primary.main' : 'white',
                    color: isUser ? 'primary.contrastText' : '#0f172a',
                    px: 1.5,
                    py: 1.2,
                    borderRadius: 3,
                    border: isUser ? 'none' : '1px solid rgba(15,23,42,0.08)',
                    boxShadow: isUser ? 2 : 0,
                    position: 'relative'
                  }}>
                    {!isUser && (
                      <Typography variant="caption" sx={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.8, opacity: 0.6, position: 'absolute', top: -14, left: 4 }}>
                        Asistente
                      </Typography>
                    )}
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{m.text}</Typography>
                    {m.citations && m.citations.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        {m.citations.map((c, idx) => (
                          <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <LinkIcon fontSize="small" />
                            <a href={c.url} target="_blank" rel="noreferrer">{c.title || c.url}</a>
                          </Box>
                        ))}
                      </Box>
                    )}
                  </Box>
                </Box>
              );
            })}
            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={18} />
                <Typography variant="body2">Pensando…</Typography>
              </Box>
            )}
          </Box>
        </Box>
        <Divider />
        <Box sx={{ p: 2, display: 'flex', gap: 1, bgcolor: 'white', position: 'sticky', bottom: 0, borderTop: '1px solid', borderColor: 'rgba(15,23,42,0.08)' }}>
          <TextField
            fullWidth
            size="small"
            placeholder='Ej: "buscar partidos de Perú 2025" o "resumen selección 2025"'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            multiline
            minRows={1}
            maxRows={3}
          />
          <Button variant="contained" onClick={send} endIcon={<SendIcon />} disabled={loading} sx={{ borderRadius: 2, px: 3 }}>Enviar</Button>
        </Box>
      </Drawer>
    </>
  );
};

export default ChatbotWidget;


