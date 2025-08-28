#!/usr/bin/env python3
import csv
import json
import re
import sys

class PIIFinder:
    def __init__(self):
        self.phone_regex = re.compile(r'\b\d{10}\b')
        self.aadhar_regex = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
        self.passport_regex = re.compile(r'\b[A-PR-WY][0-9]{6,7}\b')
        self.upi_regex = re.compile(r'[\w.-]+@(upi|okicici|axl|ybl|paytm|okaxis|ibl|sbi|phonepe|kotak|hdfc|unionbank|pnb|canara|indianbank|yesbank)')
        
    def check_standalone(self, text):
        text_str = str(text)
        return bool(self.phone_regex.search(text_str) or 
                   self.aadhar_regex.search(text_str) or 
                   self.passport_regex.search(text_str) or 
                   self.upi_regex.search(text_str))
    
    def check_combinatorial(self, data):
        name_found = any(key.lower() in ['name', 'first_name', 'last_name', 'full_name'] and data.get(key) for key in data)
        email_found = any(key.lower() in ['email', 'email_address'] and data.get(key) for key in data)
        address_count = sum(1 for key in data if key.lower() in ['address', 'street', 'city', 'pin_code', 'pincode', 'zipcode'] and data.get(key))
        device_found = any(key.lower() in ['device_id', 'ip_address'] and data.get(key) for key in data)
        user_context = any(key.lower() in ['customer_id', 'user_id', 'username'] and data.get(key) for key in data)
        
        return (name_found and email_found) or (address_count >= 2) or (device_found and user_context)
    
    def hide_data(self, value):
        if not isinstance(value, str):
            value = str(value)
            
        value = self.phone_regex.sub(lambda m: m.group()[:2] + 'XXXXXX' + m.group()[-2:], value)
        value = self.aadhar_regex.sub(lambda m: m.group().replace(' ', '')[:4] + 'XXXXXXXX' + m.group().replace(' ', '')[-4:], value)
        value = self.passport_regex.sub(lambda m: m.group()[0] + 'XXXXXX', value)
        value = self.upi_regex.sub(lambda m: 'XXX' + m.group()[m.group().find('@'):], value)
        
        return value

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 detector_full_candidate_name.py input.csv")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = "redacted_output_candidate_full_name.csv"
    
    detector = PIIFinder()
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            output_data = []
            
            for row in reader:
                record_id = row['record_id']
                json_str = row['Data_json']
                
                try:
                    data = json.loads(json_str)
                    has_pii = (detector.check_standalone(json_str) or 
                              detector.check_combinatorial(data))
                    
                    if has_pii:
                        redacted = {k: detector.hide_data(v) for k, v in data.items()}
                        output_json = json.dumps(redacted)
                    else:
                        output_json = json_str
                    
                    output_data.append([record_id, output_json, str(has_pii).upper()])
                    
                except json.JSONDecodeError:
                    output_data.append([record_id, json_str, 'FALSE'])
                except Exception:
                    output_data.append([record_id, json_str, 'FALSE'])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['record_id', 'redacted_data_json', 'is_pii'])
            writer.writerows(output_data)
            
        print(f"Processed {len(output_data)} records. Output: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
