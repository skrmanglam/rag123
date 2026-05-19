#!/usr/bin/env python3
"""
Simple script to upload FAQ CSV via API
Usage: python upload_faq.py <bot_id> <csv_file>
"""


import sys
import requests


def upload_faq(bot_id, csv_file):
   """Upload FAQ CSV to bot via API"""
  
   url = f"http://localhost:8000/bots/{bot_id}/faq/upload"
  
   try:
       with open(csv_file, 'rb') as f:
           files = {'file': (csv_file, f, 'text/csv')}
           response = requests.post(url, files=files)
      
       if response.status_code == 200:
           result = response.json()
           print("✅ FAQ uploaded successfully!")
           stats = result.get('stats', {})
           print(f"   Added: {stats.get('added', 0)}")
           print(f"   Skipped: {stats.get('skipped', 0)}")
           print(f"   Total: {stats.get('total', 0)}")
          
           if stats.get('skipped', 0) > 0:
               print("\n⚠️  Some FAQs were skipped (likely duplicates)")
               print("   To re-upload, first delete existing FAQs:")
               print(f"   curl -X DELETE http://localhost:8000/bots/{bot_id}/faq")
          
           return True
       else:
           print(f"❌ Error: {response.status_code}")
           print(response.text)
           return False
          
   except FileNotFoundError:
       print(f"❌ File not found: {csv_file}")
       return False
   except requests.exceptions.ConnectionError:
       print("❌ Cannot connect to API. Make sure it's running:")
       print("   python main_api.py")
       return False
   except Exception as e:
       print(f"❌ Error: {str(e)}")
       return False


if __name__ == "__main__":
   if len(sys.argv) != 3:
       print("Usage: python upload_faq.py <bot_id> <csv_file>")
       print("Example: python upload_faq.py customer_support_bot sample_faq.csv")
       sys.exit(1)
  
   bot_id = sys.argv[1]
   csv_file = sys.argv[2]
  
   print(f"Uploading {csv_file} to bot: {bot_id}")
   success = upload_faq(bot_id, csv_file)
  
   if success:
       print("\n✨ Now try asking in Streamlit:")
       print("   'tell me about warranty?'")
       print("   'how do I return a product?'")
  
   sys.exit(0 if success else 1)