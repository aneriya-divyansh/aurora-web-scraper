from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import json
import os
import time
from datetime import datetime
from universal_product_extractor import UniversalProductExtractor
import threading
import queue

app = Flask(__name__)

# Global variables for managing scraping tasks
scraping_tasks = {}
task_queue = queue.Queue()

class ScrapingTask:
    def __init__(self, task_id, url, max_pages, use_ocr):
        self.task_id = task_id
        self.url = url
        self.max_pages = max_pages
        self.use_ocr = use_ocr
        self.status = "pending"
        self.progress = 0
        self.results = None
        self.error = None
        self.start_time = None
        self.end_time = None

def run_scraping_task(task):
    """Run scraping task in background thread"""
    try:
        task.status = "running"
        task.start_time = datetime.now()
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize extractor
        extractor = UniversalProductExtractor()
        
        # Run extraction
        result = extractor.extract_products(
            url=task.url,
            num_pages=task.max_pages
        )
        
        task.results = result
        task.status = "completed"
        task.end_time = datetime.now()
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.end_time = datetime.now()
    finally:
        if 'loop' in locals():
            loop.close()

def background_worker():
    """Background worker to process scraping tasks"""
    while True:
        try:
            task = task_queue.get(timeout=1)
            run_scraping_task(task)
            task_queue.task_done()
        except queue.Empty:
            continue

# Start background worker
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    data = request.get_json()
    
    # If infinite scrolling is selected, force OCR fallback
    use_ocr = data.get('use_ocr', False)
    if data.get('infinite_scroll', False):
        use_ocr = True
    
    # Generate unique task ID
    task_id = f"task_{int(time.time())}"
    
    # Create new task
    task = ScrapingTask(
        task_id=task_id,
        url=data.get('url'),
        max_pages=int(data.get('max_pages', 1)),
        use_ocr=use_ocr
    )
    
    # Add to global tasks and queue
    scraping_tasks[task_id] = task
    task_queue.put(task)
    
    return jsonify({
        'task_id': task_id,
        'status': 'started',
        'estimated_time': 120 if use_ocr else 30  # 2 mins for OCR
    })

@app.route('/api/task-status/<task_id>')
def task_status(task_id):
    if task_id not in scraping_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = scraping_tasks[task_id]
    
    response = {
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'url': task.url,
        'max_pages': task.max_pages,
        'use_ocr': task.use_ocr
    }
    
    if task.start_time:
        response['start_time'] = task.start_time.isoformat()
    
    if task.end_time:
        response['end_time'] = task.end_time.isoformat()
        if task.start_time:
            duration = (task.end_time - task.start_time).total_seconds()
            response['duration'] = f"{duration:.2f}s"
    
    if task.error:
        response['error'] = task.error
    
    if task.results:
        response['results'] = {
            'total_products': len(task.results.get('products', [])),
            'total_pages': task.results.get('total_pages_scraped', 0),
            'extraction_method': task.results.get('extraction_method', 'unknown'),
            'ocr_used': task.results.get('ocr_used', False)
        }
    
    return jsonify(response)

@app.route('/api/task-results/<task_id>')
def task_results(task_id):
    if task_id not in scraping_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = scraping_tasks[task_id]
    
    if task.status != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    return jsonify(task.results)

@app.route('/api/download-results/<task_id>')
def download_results(task_id):
    if task_id not in scraping_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = scraping_tasks[task_id]
    
    if task.status != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aurora_results_{timestamp}.json"
    
    # Save results to file
    results_file = os.path.join('downloads', filename)
    os.makedirs('downloads', exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(task.results, f, indent=2, default=str)
    
    return send_file(results_file, as_attachment=True, download_name=filename)

@app.route('/api/tasks')
def list_tasks():
    tasks = []
    for task_id, task in scraping_tasks.items():
        tasks.append({
            'task_id': task_id,
            'url': task.url,
            'status': task.status,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None
        })
    
    return jsonify(tasks)

if __name__ == '__main__':
    # Create downloads directory
    os.makedirs('downloads', exist_ok=True)
    
    print("🚀 Starting Aurora Web Scraper Frontend...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🔧 Make sure the backend proxy is running: python backend_proxy.py")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 