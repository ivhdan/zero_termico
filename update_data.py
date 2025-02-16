import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def load_existing_data():
    file_path = 'zero_termico_data.csv'
    try:
        return pd.read_csv(file_path)
    except:
        return pd.DataFrame(columns=['date', 'level', 'year', 'month'])

def extract_zero_termico():
    url = "https://www.nimbus.it/italiameteo/previpiemonte.htm"
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_blocks = soup.find_all('p')
        
        data = []
        current_date = None
        
        for block in text_blocks:
            text = block.text.strip()
            date_match = re.search(r'(\d{1,2})\s*(GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE)\s*(\d{4})', text, re.IGNORECASE)
            
            if date_match:
                current_date = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
                date_obj = datetime.strptime(current_date, '%d/%B/%Y')
            
            zero_match = re.search(r'Zero gradi a (\d+)-(\d+)', text)
            
            if zero_match and current_date:
                min_alt = int(zero_match.group(1))
                max_alt = int(zero_match.group(2))
                media_alt = (min_alt + max_alt) // 2
                
                data.append({
                    'date': current_date,
                    'level': media_alt,
                    'year': date_obj.year,
                    'month': date_obj.month
                })
        
        return data
        
    except Exception as e:
        print(f"Errore durante l'estrazione: {e}")
        return None

def main():
    print("Inizio aggiornamento dati zero termico...")
    
    # Carica dati esistenti
    print("Caricamento dati esistenti...")
    df_existing = load_existing_data()
    
    # Estrai nuovi dati
    print("Estrazione nuovi dati da Nimbus...")
    new_data = extract_zero_termico()
    
    if new_data:
        df_new = pd.DataFrame(new_data)
        
        # Combina e rimuovi duplicati
        print("Aggiornamento dataset...")
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['date'])
        
        # Ordina
        df_combined = df_combined.sort_values(['year', 'month', 'date'])
        
        # Salva
        print("Salvataggio dati aggiornati...")
        df_combined.to_csv('zero_termico_data.csv', index=False)
        print("Aggiornamento completato con successo!")
    else:
        print("Nessun nuovo dato estratto.")

if __name__ == "__main__":
    main()
