import json
import pandas as pd
from typing import Dict, List, Any

class TableFormatter:
    def __init__(self):
        self.tables = {}
    
    def format_extracted_data(self, data: Dict[str, Any], output_format: str = "console") -> str:
        """
        Format extracted data into tables
        
        Args:
            data: Extracted data from AI parser
            output_format: "console", "csv", or "html"
            
        Returns:
            Formatted table string
        """
        
        if not data.get('data'):
            return "No data to format"
        
        # Group data by type
        grouped_data = {}
        for item in data['data']:
            item_type = item.get('type', 'unknown')
            if item_type not in grouped_data:
                grouped_data[item_type] = []
            grouped_data[item_type].append(item)
        
        # Create tables for each data type
        tables = {}
        
        for data_type, items in grouped_data.items():
            if data_type == 'price':
                table = self._create_price_table(items)
            elif data_type == 'product_name':
                table = self._create_product_table(items)
            elif data_type == 'rating':
                table = self._create_rating_table(items)
            elif data_type == 'location':
                table = self._create_location_table(items)
            else:
                table = self._create_generic_table(items, data_type)
            
            tables[data_type] = table
        
        # Format output based on requested format
        if output_format == "csv":
            return self._format_csv(tables)
        elif output_format == "html":
            return self._format_html(tables)
        else:
            return self._format_console(tables)
    
    def _create_price_table(self, items: List[Dict]) -> pd.DataFrame:
        """Create a price table"""
        rows = []
        for i, item in enumerate(items, 1):
            rows.append({
                'ID': i,
                'Price': item.get('value', 'N/A'),
                'Currency': item.get('currency', 'Unknown'),
                'Type': 'Price'
            })
        return pd.DataFrame(rows)
    
    def _create_product_table(self, items: List[Dict]) -> pd.DataFrame:
        """Create a product table"""
        rows = []
        for i, item in enumerate(items, 1):
            # Clean up product names
            name = item.get('value', 'N/A')
            if len(name) > 100:
                name = name[:97] + "..."
            
            rows.append({
                'ID': i,
                'Product Name': name,
                'Type': 'Product'
            })
        return pd.DataFrame(rows)
    
    def _create_rating_table(self, items: List[Dict]) -> pd.DataFrame:
        """Create a rating table"""
        rows = []
        for i, item in enumerate(items, 1):
            rows.append({
                'ID': i,
                'Rating': item.get('value', 'N/A'),
                'Scale': item.get('scale', 'N/A'),
                'Type': 'Rating'
            })
        return pd.DataFrame(rows)
    
    def _create_location_table(self, items: List[Dict]) -> pd.DataFrame:
        """Create a location table"""
        rows = []
        for i, item in enumerate(items, 1):
            rows.append({
                'ID': i,
                'Location': item.get('value', 'N/A'),
                'Type': 'Location'
            })
        return pd.DataFrame(rows)
    
    def _create_generic_table(self, items: List[Dict], data_type: str) -> pd.DataFrame:
        """Create a generic table for unknown data types"""
        rows = []
        for i, item in enumerate(items, 1):
            rows.append({
                'ID': i,
                'Value': item.get('value', 'N/A'),
                'Type': data_type.title()
            })
        return pd.DataFrame(rows)
    
    def _format_console(self, tables: Dict[str, pd.DataFrame]) -> str:
        """Format tables for console output"""
        output = []
        
        for table_name, df in tables.items():
            output.append(f"\n📊 {table_name.upper()} TABLE")
            output.append("=" * 60)
            output.append(df.to_string(index=False))
            output.append(f"\nTotal {table_name}: {len(df)} items")
        
        return "\n".join(output)
    
    def _format_csv(self, tables: Dict[str, pd.DataFrame]) -> str:
        """Format tables as CSV"""
        output = []
        
        for table_name, df in tables.items():
            csv_content = df.to_csv(index=False)
            output.append(f"# {table_name.upper()} TABLE")
            output.append(csv_content)
            output.append("")  # Empty line between tables
        
        return "\n".join(output)
    
    def _format_html(self, tables: Dict[str, pd.DataFrame]) -> str:
        """Format tables as HTML"""
        output = ["<html><head><title>Extracted Data</title></head><body>"]
        
        for table_name, df in tables.items():
            output.append(f"<h2>{table_name.upper()} TABLE</h2>")
            output.append(df.to_html(index=False, classes='table table-striped'))
            output.append(f"<p>Total {table_name}: {len(df)} items</p>")
        
        output.append("</body></html>")
        return "\n".join(output)

def interactive_table_formatter():
    """Interactive table formatter"""
    
    print("📊 Table Formatter for Extracted Data")
    print("=" * 50)
    
    # Ask for JSON file
    print("\nAvailable extracted data files:")
    import os
    json_files = [f for f in os.listdir('.') if f.startswith('extracted_data_') and f.endswith('.json')]
    
    if not json_files:
        print("No extracted data files found. Please run the AI parser first.")
        return
    
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file}")
    
    try:
        choice = int(input("\nSelect file number: "))
        if 1 <= choice <= len(json_files):
            file_path = json_files[choice - 1]
        else:
            print("Invalid choice, using first file")
            file_path = json_files[0]
    except ValueError:
        print("Invalid input, using first file")
        file_path = json_files[0]
    
    # Load data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📋 Loading data from: {file_path}")
        
        # Ask for output format
        print("\nOutput format options:")
        print("1. Console (default)")
        print("2. CSV")
        print("3. HTML")
        
        format_choice = input("\nSelect format (1-3, default=1): ").strip()
        
        if format_choice == "2":
            output_format = "csv"
        elif format_choice == "3":
            output_format = "html"
        else:
            output_format = "console"
        
        # Format data
        formatter = TableFormatter()
        formatted_output = formatter.format_extracted_data(data, output_format)
        
        # Display or save output
        if output_format == "console":
            print(formatted_output)
        else:
            # Save to file
            output_file = f"formatted_data_{file_path.replace('.json', '')}.{output_format}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            print(f"\n💾 Formatted data saved to: {output_file}")
            
            # Also show preview
            print("\n📋 Preview:")
            print("-" * 50)
            lines = formatted_output.split('\n')[:20]
            print('\n'.join(lines))
            if len(formatted_output.split('\n')) > 20:
                print("... (truncated)")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error processing file: {e}")

if __name__ == "__main__":
    interactive_table_formatter() 