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
        if self.phone_regex.search(text_str):
            return True
        if self.aadhar_regex.search(text_str):
            return True
        if self.passport_regex.search(text_str):
            return True
        if self.upi_regex.search(text_str):
            return True
        return False
    
    def check_combinatorial(self, data):
        name_found = False
        email_found = False
        address_count = 0
        
        for key, value in data.items():
            key_low = key.lower()
            if not value:
                continue
                
            if key_low in ['name', 'first_name', 'last_name', 'full_name']:
                name_found = True
            elif key_low in ['email', 'email_address']:
                email_found = True
            elif key_low in ['address', 'street', 'city', 'pin_code', 'pincode', 'zipcode']:
                address_count += 1
        
        if name_found and email_found:
            return True
        if address_count >= 2:
            return True
            
        return False
    
    def hide_data(self, value):
        if not isinstance(value, str):
            value = str(value)
            
        value = self.phone_regex.sub(lambda m: m.group()[:3] + 'XXXXX' + m.group()[8:], value)
        value = self.aadhar_regex.sub(lambda m: m.group().replace(' ', '')[:4] + 'XXXX' + m.group().replace(' ', '')[8:], value)
        value = self.passport_regex.sub(lambda m: m.group()[0] + 'XXXXXX', value)
        value = self.upi_regex.sub(lambda m: 'XXX' + m.group()[m.group().find('@'):], value)
        
        return value

def main():
    if len(sys.argv) == 2:
        input_file = sys.argv[1]
    else:
        input_file = "iscp_pii_dataset_-_Sheet1.csv"
    
    output_file = "redacted_output_candidate_full_name.csv"
    
    finder = PIIFinder()
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            results = []
            
            for row in reader:
                record_id = row['record_id']
                json_data = row['data_json']
                
                try:
                    data = json.loads(json_data)
                    standalone = finder.check_standalone(json_data)
                    combinatorial = finder.check_combinatorial(data)
                    has_pii = standalone or combinatorial
                    
                    if has_pii:
                        hidden_data = {}
                        for k, v in data.items():
                            hidden_data[k] = finder.hide_data(v)
                        output_json = json.dumps(hidden_data)
                    else:
                        output_json = json_data
                        
                    results.append([record_id, output_json, str(has_pii).upper()])
                    
                except:
                    results.append([record_id, json_data, 'FALSE'])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(['record_id', 'redacted_data_json', 'is_pii'])
            for row in results:
                writer.writerow(row)
                
        print(f"Processed {len(results)} records from {input_file}")
        print(f"Output saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()