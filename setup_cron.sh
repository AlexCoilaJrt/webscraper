#!/bin/bash
# Script para configurar cron jobs de scraping automático

echo "🔧 Configurando scraping automático..."

# Crear backup del crontab actual
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "No hay crontab existente"

# Agregar nuevos cron jobs
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Noticias matutinas (8:00 AM)") | crontab -
(crontab -l 2>/dev/null; echo "0 8 * * * /Users/usuario/Documents/scraping\ 2/run_auto_scraping.sh") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Noticias vespertinas (6:00 PM)") | crontab -
(crontab -l 2>/dev/null; echo "0 18 * * * /Users/usuario/Documents/scraping\ 2/run_auto_scraping.sh") | crontab -
(crontab -l 2>/dev/null; echo "") | crontab -
(crontab -l 2>/dev/null; echo "# Scraping automático - Diario Sin Fronteras (12:00 PM)") | crontab -
(crontab -l 2>/dev/null; echo "0 12 * * * /Users/usuario/Documents/scraping\ 2/run_auto_scraping.sh") | crontab -

echo "✅ Cron jobs configurados exitosamente"
echo "📋 Para ver los cron jobs configurados: crontab -l"
echo "📋 Para ver los logs: tail -f auto_scraping.log"
echo "📋 Para eliminar todos los cron jobs: crontab -r"
