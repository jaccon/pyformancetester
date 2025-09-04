from flask import Flask, request, render_template, jsonify, redirect, url_for, send_from_directory
import os
import uuid
import threading
import time
from _pyFormanceTest import WebsitePerformanceTester

app = Flask(__name__)

# Configure Flask to serve files from the reports directory
@app.route('/reports/<path:filename>')
def serve_report(filename):
    """Serve report files directly"""
    return send_from_directory('reports', filename)

# Global dictionary to store analysis jobs
analysis_jobs = {}

def analyze_website_task(job_id, url):
    """
    Function to run the website analysis in a separate thread
    """
    job = analysis_jobs[job_id]
    job['status'] = 'running'
    
    try:
        # Create a WebsitePerformanceTester instance with the progress callback
        def progress_update(percent, message, resource_info):
            job['progress'] = percent
            job['message'] = message
            job['resource_info'] = resource_info
        
        # Initialize the tester with the callback
        tester = WebsitePerformanceTester(url, progress_callback=progress_update)
        
        # Run the analysis
        tester.analyze_website()
        
        # Generate the report with a fixed name for easier access
        try:
            # The generate_report method returns a tuple of (csv_path, html_path)
            _, html_report_path = tester.generate_report(fixed_name=True)
            
            # Store the report path and HTML content if the report was generated
            if html_report_path and os.path.exists(html_report_path):
                # Save the full path to the report file
                job['report_path'] = html_report_path
                
                # Also save the HTML content for backward compatibility
                with open(html_report_path, 'r', encoding='utf-8') as f:
                    job['result_html'] = f.read()
            else:
                job['result_html'] = "<div class='center'>Relatório HTML não foi gerado, mas a análise foi concluída.</div>"
                job['report_path'] = None
        except Exception as e:
            print(f"Erro ao gerar relatório: {str(e)}")
            job['error'] = f"Erro ao gerar relatório: {str(e)}"
            job['report_path'] = None
                
        job['status'] = 'completed'
        
    except Exception as e:
        job['status'] = 'error'
        job['error'] = str(e)
        job['message'] = f"Erro na análise: {str(e)}"
        print(f"Erro na análise: {str(e)}")

@app.route('/')
def index():
    """Main page with the URL input form"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Start a new analysis job"""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Create a new job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job data
    analysis_jobs[job_id] = {
        'url': url,
        'status': 'initialized',
        'progress': 0,
        'message': 'Iniciando análise...',
        'resource_info': {},
        'result_html': None,
        'error': None,
        'created_at': time.time()
    }
    
    # Start the analysis in a separate thread
    thread = threading.Thread(target=analyze_website_task, args=(job_id, url))
    thread.daemon = True
    thread.start()
    
    # Redirect to the loading page
    return redirect(url_for('loading', job_id=job_id))

@app.route('/loading/<job_id>')
def loading(job_id):
    """Loading page that polls for job progress"""
    if job_id not in analysis_jobs:
        return render_template('error.html', error="Análise não encontrada. Por favor, tente novamente.")
    
    return render_template('loading.html', job_id=job_id)

@app.route('/job_status/<job_id>')
def job_status(job_id):
    """API endpoint to get the current status of a job"""
    if job_id not in analysis_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = analysis_jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message'],
        'resource_info': job['resource_info'],
        'error': job['error']
    })

@app.route('/results/<job_id>')
def results(job_id):
    """Show the analysis results"""
    if job_id not in analysis_jobs:
        return render_template('error.html', error="Análise não encontrada. Por favor, tente novamente.")
    
    job = analysis_jobs[job_id]
    
    if job['status'] == 'error':
        return render_template('error.html', error=job['error'])
    elif job['status'] == 'completed':
        # Se temos um caminho para o relatório, usar diretamente
        if job.get('report_path') and os.path.exists(job['report_path']):
            try:
                # Verificar se temos o caminho do relatório
                report_path = job['report_path']
                
                # Copiar o relatório para um nome fixo para facilitar o acesso
                domain = job['url'].split('://')[1].split('/')[0].replace(".", "_")
                fixed_report_path = os.path.join('reports', f"latest_{domain}.html")
                
                # Copiar o relatório para o arquivo com nome fixo
                import shutil
                shutil.copy2(report_path, fixed_report_path)
                print(f"Relatório copiado para: {fixed_report_path}")
                
                # Ler o conteúdo do relatório
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_html = f.read()
                    
                # Retornar o conteúdo HTML diretamente no template
                return render_template('result.html', report_html=report_html)
            except Exception as e:
                print(f"Erro ao processar o relatório: {str(e)}")
                return render_template('error.html', error=f"Erro ao processar o relatório: {str(e)}")
        else:
            return render_template('error.html', error="O relatório HTML não foi gerado corretamente.")
    else:
        # Se o job ainda estiver em execução, redirecionar de volta para a página de carregamento
        return redirect(url_for('loading', job_id=job_id))

# Clean up old jobs (could be run periodically)
def cleanup_old_jobs():
    current_time = time.time()
    for job_id in list(analysis_jobs.keys()):
        if current_time - analysis_jobs[job_id].get('created_at', 0) > 3600:  # 1 hour
            del analysis_jobs[job_id]

if __name__ == '__main__':
    app.run(debug=True)
