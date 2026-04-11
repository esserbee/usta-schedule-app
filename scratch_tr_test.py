import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def fetch_tennis_record_stats(player_name):
    """Fetch estimated dynamic rating and yearly record from TennisRecord.com"""
    encoded_name = quote(player_name)
    url = f"https://www.tennisrecord.com/adult/profile.aspx?playername={encoded_name}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    print(f"Fetching TR for: {player_name}")
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            return None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. Extract Rating
        rating = None
        rating_section = soup.find(string=re.compile(r'Estimated Dynamic Rating', re.I))
        if rating_section:
            container_text = rating_section.parent.get_text()
            if not container_text:
                 container_text = rating_section.parent.parent.get_text()
            match = re.search(r'(\d\.\d{4})', container_text)
            if match:
                rating = match.group(1)
        
        print(f"Found Rating: {rating}")
        
        # 2. Extract Yearly Table
        tr_stats = []
        table = soup.find('table', {'class': 'grid'}) or soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 4:
                    year_text = tds[0].get_text(strip=True)
                    if year_text.isdigit() and len(year_text) == 4:
                        tr_stats.append({
                            'year': year_text,
                            'total': tds[1].get_text(strip=True),
                            'wins': tds[2].get_text(strip=True),
                            'losses': tds[3].get_text(strip=True),
                            'win_pct': tds[4].get_text(strip=True) if len(tds) > 4 else ''
                        })
        
        print(f"Found {len(tr_stats)} years of stats")
        return {
            'rating': rating,
            'yearly_record': tr_stats,
            'url': url
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_names = ["Sudipta Biswas", "John Doe"]
    for name in test_names:
        stats = fetch_tennis_record_stats(name)
        print(stats)
        print("-" * 20)
