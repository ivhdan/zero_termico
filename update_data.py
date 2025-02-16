import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

def load_existing_data():
    file_path = 'zero_termico_data.csv'
    try:
        df = pd.read_csv(file_path)
        # Estrai anno e mese dalla colonna date
        df['date'] = pd.to_datetime(df['date'], format='%d/%B/%Y')
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        return df
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
            
            zero_match = re.search(r'Zero gradi a (\d+)-(\d+)', text)
            
            if zero_match and current_date:
                min_alt = int(zero_match.group(1))
                max_alt = int(zero_match.group(2))
                media_alt = (min_alt + max_alt) // 2
                
                data.append({
                    'date': current_date,
                    'level': media_alt
                })
        
        return data
        
    except Exception as e:
        print(f"Errore durante l'estrazione: {e}")
        return None

def generate_monthly_page(year, month, data):
    month_names = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                   'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    
    month_name = month_names[month - 1]
    
    html_template = f'''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zero Termico - {month_name} {year}</title>
        <link rel="stylesheet" href="../css/style.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>Zero Termico - {month_name} {year}</h1>
            <div class="chart-container">
                <canvas id="monthChart"></canvas>
            </div>
            <div class="navigation">
                <a href="../temp_graph.html">Torna all'indice</a>
            </div>
        </div>
        <script src="../js/charts.js"></script>
        <script>
            const data = {data.to_json(orient='records')};
            createMonthlyChart('monthChart', {{
                dates: data.map(d => d.date),
                levels: data.map(d => d.level)
            }});
        </script>
    </body>
    </html>
    '''
    
    # Crea la directory se non esiste
    os.makedirs(f'docs/{year}', exist_ok=True)
    
    # Salva la pagina
    with open(f'docs/{year}/{month_name.lower()}.html', 'w', encoding='utf-8') as f:
        f.write(html_template)

def update_main_page(all_data):
    years = sorted(all_data['year'].unique())
    
    html_content = '''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zero Termico - Grafici Mensili</title>
        <link rel="stylesheet" href="css/style.css">
    </head>
    <body>
        <div class="container">
            <h1>Zero Termico - Archivio Grafici</h1>
    '''
    
    for year in years:
        year_data = all_data[all_data['year'] == year]
        months = sorted(year_data['month'].unique())
        
        html_content += f'''
            <div class="year-section">
                <h2>{year}</h2>
                <div class="month-grid">
        '''
        
        month_names = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                      'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        
        for month in months:
            month_name = month_names[month - 1]
            html_content += f'''
                    <a href="{year}/{month_name.lower()}.html">{month_name}</a>
            '''
        
        html_content += '''
                </div>
            </div>
        '''
    
    html_content += '''
        </div>
    </body>
    </html>
    '''
    
    with open('docs/temp_graph.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

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
        
        # Salva CSV principale
        print("Salvataggio dati aggiornati...")
        df_combined.to_csv('zero_termico_data.csv', index=False)
        
        # Genera pagine mensili
        print("Generazione pagine mensili...")
        for year in df_combined['year'].unique():
            for month in df_combined['month'].unique():
                monthly_data = df_combined[
                    (df_combined['year'] == year) & 
                    (df_combined['month'] == month)
                ]
                if not monthly_data.empty:
                    generate_monthly_page(year, month, monthly_data)
        
        # Aggiorna pagina principale
        print("Aggiornamento pagina principale...")
        update_main_page(df_combined)
        
        print("Aggiornamento completato con successo!")
    else:
        print("Nessun nuovo dato estratto.")

if __name__ == "__main__":
    main()
