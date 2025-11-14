import argparse
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import uuid

# --- CONFIGURATION ---
DB_FILE = 'articles.db'
TABLE_NAME = 'articles'
DATE_FORMAT = '%Y-%m-%d'

# --- DATABASE FUNCTIONS ---

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def setup_database(conn):
    """Creates the 'articles' table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT,
            link TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            published_date TEXT NOT NULL
        )
    """)
    conn.commit()

# --- MOCK DATA FETCHING (Replace with actual NewsAPI/Scraping) ---

def fetch_mock_data(source_filter=None):
    """
    Mocks fetching news articles. In a real application, this function 
    would contain logic for NewsAPI calls or web scraping (requests + BeautifulSoup).
    
    Returns a list of dictionaries.
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    all_articles = [
        {
            'title': 'AI Breakthrough: New LLM achieves record performance',
            'summary': 'Researchers have unveiled a massive new language model...',
            'link': 'http://sourcea.com/article1',
            'source': 'SourceA (Tech Weekly)',
            'published_date': today.strftime(DATE_FORMAT)
        },
        {
            'title': 'Global Markets Rally on Tech Stocks Optimism',
            'summary': 'The stock market saw significant gains driven by...',
            'link': 'http://sourceb.com/article2',
            'source': 'SourceB (Finance News)',
            'published_date': today.strftime(DATE_FORMAT)
        },
        {
            'title': 'The Future of Robotics in Manufacturing: A Deep Dive',
            'summary': 'Automation continues to reshape factory floors globally.',
            'link': 'http://sourcea.com/article3',
            'source': 'SourceA (Tech Weekly)',
            'published_date': yesterday.strftime(DATE_FORMAT)
        },
        {
            'title': 'New Policy Changes Affecting Small Businesses',
            'summary': 'Government introduces incentives for local entrepreneurs.',
            'link': 'http://sourcec.com/article4',
            'source': 'SourceC (Policy Hub)',
            'published_date': today.strftime(DATE_FORMAT)
        },
        {
            'title': 'AI Breakthrough: New LLM achieves record performance', # Duplicate title/summary, different link
            'summary': 'Researchers have unveiled a massive new language model...',
            'link': 'http://sourcea.com/article1_v2',
            'source': 'SourceA (Tech Weekly)',
            'published_date': today.strftime(DATE_FORMAT)
        },
    ]

    if source_filter:
        all_articles = [a for a in all_articles if a['source'].lower() == source_filter.lower()]
        
    return all_articles

def save_articles(articles):
    """Saves a list of articles to the database with deduplication."""
    if not articles:
        print("No articles to save.")
        return

    # Use Pandas for quick in-memory deduplication based on 'link'
    df = pd.DataFrame(articles)
    
    # Basic Deduplication: Drop duplicates based on the 'link' (which is UNIQUE in the DB)
    df_deduped = df.drop_duplicates(subset=['link'], keep='first')
    
    # Add a unique ID for the primary key
    df_deduped['id'] = [str(uuid.uuid4()) for _ in range(len(df_deduped))]

    conn = get_db_connection()
    new_articles_count = 0
    duplicate_count = 0

    print(f"Attempting to insert {len(df_deduped)} unique articles...")
    
    for _, row in df_deduped.iterrows():
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (id, title, summary, link, source, published_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row['id'],
                row['title'],
                row['summary'],
                row['link'],
                row['source'],
                row['published_date']
            ))
            new_articles_count += 1
        except sqlite3.IntegrityError:
            # This catches duplicates based on the UNIQUE constraint on 'link'
            duplicate_count += 1
        except Exception as e:
            print(f"Error inserting article {row['title']}: {e}")

    conn.commit()
    conn.close()
    print(f"\n--- Save Results ---")
    print(f"Total processed: {len(articles)}")
    print(f"New articles inserted: {new_articles_count}")
    print(f"Skipped as duplicates (in batch or DB): {len(articles) - new_articles_count}")


# --- QUERY AND EXPORT FUNCTIONS ---

def build_query(args):
    """Constructs the SQL query and parameters based on CLI arguments."""
    base_query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = {}
    
    # Filter by Source
    if args.source:
        # Use LIKE for case-insensitive partial match
        base_query += " AND source LIKE :source"
        params['source'] = f'%{args.source}%'
        
    # Filter by Keyword in title or summary
    if args.keyword:
        base_query += " AND (title LIKE :keyword OR summary LIKE :keyword)"
        params['keyword'] = f'%{args.keyword}%'
        
    # Filter by Date (e.g., --date 2024-10-25)
    if args.date:
        try:
            # Ensure the date is valid and format correctly
            datetime.strptime(args.date, DATE_FORMAT)
            base_query += " AND published_date = :date"
            params['date'] = args.date
        except ValueError:
            print(f"Warning: Invalid date format provided: {args.date}. Required format is YYYY-MM-DD. Ignoring date filter.")

    base_query += " ORDER BY published_date DESC"
    
    return base_query, params

def execute_query(args):
    """Fetches articles from the DB based on the CLI filters."""
    query, params = build_query(args)
    conn = get_db_connection()
    
    # Use pandas to easily read the SQL query results into a DataFrame
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df.drop(columns=['id']) # Hide the internal ID column for display/export
    except Exception as e:
        print(f"Database query failed: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def export_data(df, output_file, export_format):
    """Exports the resulting DataFrame to the specified file format."""
    if df.empty:
        print("No results to export.")
        return
        
    print(f"Exporting {len(df)} articles to {output_file}...")

    try:
        if export_format == 'csv':
            df.to_csv(output_file, index=False)
            print(f"Successfully exported to CSV: {output_file}")
            
        elif export_format == 'excel':
            # Note: Requires openpyxl installed (pip install openpyxl)
            df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"Successfully exported to Excel: {output_file}")
            
        elif export_format == 'json':
            df.to_json(output_file, orient='records', indent=4)
            print(f"Successfully exported to JSON: {output_file}")
            
        else:
            print(f"Error: Unsupported export format '{export_format}'.")
            
    except Exception as e:
        print(f"An error occurred during export: {e}")


# --- CLI ARGPARSE SETUP AND MAIN LOGIC ---

def setup_cli_parser():
    """Sets up the ArgumentParser with subcommands."""
    parser = argparse.ArgumentParser(
        description="A comprehensive CLI News Aggregator.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(
        dest='command', 
        required=True, 
        help='Available commands'
    )

    # 1. FETCH Command (Simulates scraping/API calls)
    parser_fetch = subparsers.add_parser('fetch', 
                                         help='Fetch articles and save to the database.')
    parser_fetch.add_argument('-s', '--source', type=str, 
                              help='(Optional) Filter sources during fetch (e.g., "SourceA").')
    
    # 2. QUERY Command (View aggregated data)
    parser_query = subparsers.add_parser('query', 
                                         help='Query and display stored articles in the console.')
    
    # 3. EXPORT Command (Output aggregated data to file)
    parser_export = subparsers.add_parser('export', 
                                          help='Filter stored articles and export to a file.')
                                          
    # Common Filter Arguments (Applied to QUERY and EXPORT)
    filter_group_desc = "Arguments for filtering the stored news data"
    filter_group_query = parser_query.add_argument_group('Filtering', filter_group_desc)
    filter_group_export = parser_export.add_argument_group('Filtering', filter_group_desc)
    
    for group in [filter_group_query, filter_group_export]:
        group.add_argument('-k', '--keyword', type=str, 
                            help='Filter by keyword (in title or summary).')
        group.add_argument('-s', '--source', type=str, 
                            help='Filter by news source (e.g., "SourceA").')
        group.add_argument('-d', '--date', type=str, 
                            help='Filter by publication date (format YYYY-MM-DD).')
    
    # EXPORT Specific Arguments
    parser_export.add_argument('output_file', type=str, 
                                help='The name/path of the output file (e.g., "report.csv").')
    parser_export.add_argument('-f', '--format', 
                                choices=['csv', 'excel', 'json'], 
                                default='csv',
                                help='Output format (csv, excel, json). Excel requires openpyxl.')
                                
    return parser

def main():
    """Main execution function for the CLI."""
    parser = setup_cli_parser()
    args = parser.parse_args()

    # Database Initialization (Always run this first)
    conn = get_db_connection()
    setup_database(conn)
    conn.close()

    if args.command == 'fetch':
        # 1. FETCH command logic
        print(f"--- Running FETCH command ---")
        print("NOTE: Using mock data. Replace fetch_mock_data with actual API/Scraping logic.")
        articles = fetch_mock_data(args.source)
        save_articles(articles)
        print("FETCH complete.")

    elif args.command == 'query':
        # 2. QUERY command logic
        print(f"--- Running QUERY command ---")
        df = execute_query(args)
        
        if df.empty:
            print("Query returned no results.")
            return

        print(f"\nFound {len(df)} articles matching criteria:")
        
        # Display the DataFrame nicely in the console
        print(df.to_string(index=False))
        
    elif args.command == 'export':
        # 3. EXPORT command logic
        print(f"--- Running EXPORT command ---")
        df = execute_query(args)
        
        if df.empty:
            print("Query returned no results. Nothing exported.")
            return
            
        export_data(df, args.output_file, args.format)
        
    else:
        # Should not be reached due to required=True in subparsers
        parser.print_help()

if __name__ == '__main__':
    main()