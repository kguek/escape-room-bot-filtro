import telebot
from datetime import datetime
import os
import time
import requests  # <--- AGGIUNGI QUESTO
import urllib3   # <--- AGGIUNGI QUESTO
import telebot
from datetime import datetime
# Rimuoviamo l'import di 'locale' perché non lo useremo più
import os 

# ==============================================================================
# 1. IMPOSTAZIONI DEL BOT
# ==============================================================================

# RECUPERA IL TOKEN in modo sicuro dalla variabile d'ambiente di Railway
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    print("ERRORE: La variabile d'ambiente TELEGRAM_BOT_TOKEN non è stata trovata.")
    exit()

# Inizializza il bot
bot = telebot.TeleBot(TOKEN)

# ==============================================================================
# 2. FUNZIONE DI LOGICA: ESTRAZIONE E FILTRAGGIO (Invariata)
# ==============================================================================

def estrai_prenotazioni_del_giorno(testo_completo_prenotazioni: str, data_cercata: str) -> str:
    """
    Filtra e restituisce le prenotazioni relative alla data cercata dal testo completo.
    """
    testo_completo = testo_completo_prenotazioni.strip()
    
    # 1. Trova l'inizio del blocco
    # CERCA LA DATA IN ITALIANO GENERATA DAL FALLBACK
    inizio_blocco = testo_completo.find(data_cercata + '\n')
    
    if inizio_blocco == -1:
        return f"Nessuna prenotazione trovata per il {data_cercata}."

    # Calcola l'indice di inizio del contenuto (dopo la riga della data)
    inizio_contenuto = inizio_blocco + len(data_cercata) + 1 
    testo_dopo_oggi = testo_completo[inizio_contenuto:]
    
    # 2. Trova la fine del blocco (l'inizio del giorno successivo)
    righe = testo_dopo_oggi.split('\n')
    fine_relativa = -1
    
    # Cerca la prima riga successiva che assomiglia a una nuova intestazione di data:
    # [Numero Spazio MESE_IN_MAIUSCOLO]
    for i, riga in enumerate(righe):
        parti = riga.strip().split()
        if len(parti) > 1 and parti[0].isdigit() and parti[1].isupper():
            # Trovata una riga che probabilmente è la data successiva
            fine_relativa = len('\n'.join(righe[:i]))
            break
            
    if fine_relativa == -1:
        # Se non c'è un giorno successivo, il blocco di oggi è l'ultimo
        blocco_oggi = testo_dopo_oggi.strip()
    else:
        # Prendi il testo solo fino all'inizio del giorno successivo
        blocco_oggi = testo_dopo_oggi[:fine_relativa].strip()

    if not blocco_oggi:
        return f"Nessuna prenotazione trovata per il {data_cercata}."
    
    # 3. Ricostruisce il messaggio con l'intestazione
    risultato = data_cercata + '\n' + blocco_oggi
    return risultato.strip()

# ==============================================================================
# 3. GESTIONE MESSAGGI TELEGRAM
# ==============================================================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Gestisce il comando /start e /help."""
    benvenuto = (
        "Ciao! Sono il tuo bot filtro per le prenotazioni.\n"
        "Per usarmi, **inoltra qui il messaggio completo** con le prenotazioni "
        "dalla chat di gruppo.\n\n"
        "Filtro automaticamente solo le prenotazioni per la data di **oggi**."
    )
    bot.reply_to(message, benvenuto)

@bot.message_handler(func=lambda message: True)
def handle_forwarded_message(message):
    """Gestisce tutti i messaggi INOLTRATI contenenti le prenotazioni."""
    
    # 1. Determina la data odierna nel formato richiesto (es. "17 OTTOBRE")
    data_oggi = datetime.now()
    
    # === SOLUZIONE DEFINITIVA: MAPPATURA MANUALE DEI MESI ITALIANI ===
    
    # Lista dei mesi in italiano in maiuscolo (indice 0 = Gennaio)
    mesi_italiani = [
        "GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", 
        "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"
    ]
    
    # data_oggi.month restituisce 1 (Gennaio) a 12 (Dicembre)
    nome_del_mese = mesi_italiani[data_oggi.month - 1] 
    
    # Crea la stringa di ricerca: es. "17 OTTOBRE"
    giorno_formattato = str(data_oggi.day) + ' ' + nome_del_mese
    
    # --- FINE SOLUZIONE DEFINITIVA ---

    # 2. Ottieni il testo da filtrare
    if message.text:
        testo_da_filtrare = message.text
        
        # 3. Filtra il testo
        risultato = estrai_prenotazioni_del_giorno(testo_da_filtrare, giorno_formattato)
        
        # 4. Invia il risultato all'utente (a te)
        bot.reply_to(message, risultato)
    else:
        # Messaggio di errore se non è testo
        bot.reply_to(message, "Per favore, inoltra solo il **messaggio di testo** con le prenotazioni complete.")


# ==============================================================================
# 4. AVVIO DEL BOT (IMPLEMENTAZIONE ROBUSTA)
# ==============================================================================

import time # Aggiungi questa riga all'inizio del tuo file con gli altri 'import'

print("Bot avviato e in ascolto...")

while True:
    try:
        # Avvia il polling con none_stop=True (come prima)
        bot.polling(none_stop=True, interval=0, timeout=20) 
        
    except requests.exceptions.ReadTimeout:
        # Gestisce i timeout "puliti" se il server non risponde, riprova immediatamente
        print("Timeout di lettura, riavvio polling...")
        time.sleep(1) 
        continue
    
    except (requests.exceptions.ConnectionError, urllib3.exceptions.ProtocolError) as e:
        # Gestisce la disconnessione forzata (ConnectionResetError) e altri errori di connessione
        print(f"Errore di Connessione/Protocollo: {e}. Riprovo tra 5 secondi...")
        time.sleep(5)
        continue
        
    except Exception as e:
        # Gestisce eventuali altri errori imprevisti
        print(f"Errore generico: {e}. Riprovo tra 10 secondi...")
        time.sleep(10)
        continue
