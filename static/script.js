// Intelligent Agentic RAG System - Frontend JavaScript

class RAGSystemUI {
    constructor() {
        this.apiBase = '/api';
        this.documents = [];
        this.selectedDocuments = new Set();
        this.loadingModal = null;
        this.errorModal = null;
        
        this.init();
    }

    init() {
        // Initialize Bootstrap modals
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        this.errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        this.loadDocuments();
        
        console.log('RAG System UI initialized');
    }

    setupEventListeners() {
        // Upload form
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });

        // Query form
        document.getElementById('queryForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleQuery();
        });

        // Comparison form
        document.getElementById('compareForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleComparison();
        });

        // Refresh documents
        document.getElementById('refreshDocsBtn').addEventListener('click', () => {
            this.loadDocuments();
        });

        // Clear results
        document.getElementById('clearResultsBtn').addEventListener('click', () => {
            this.clearResults();
        });

        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.updateUploadButton(e.target.files.length);
        });
    }

    updateUploadButton(fileCount) {
        const btn = document.getElementById('uploadBtn');
        const icon = btn.querySelector('i');
        
        if (fileCount === 0) {
            btn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload & Analyze';
            btn.disabled = false;
        } else if (fileCount === 1) {
            btn.innerHTML = `<i class="fas fa-upload me-2"></i>Upload 1 Document`;
            btn.disabled = false;
        } else {
            btn.innerHTML = `<i class="fas fa-upload me-2"></i>Upload ${fileCount} Documents`;
            btn.disabled = false;
        }
    }

    showLoading(title = 'Processing...', subtitle = 'Please wait while we analyze your documents') {
        document.getElementById('loadingText').textContent = title;
        document.getElementById('loadingSubtext').textContent = subtitle;
        this.loadingModal.show();
    }

    hideLoading() {
        this.loadingModal.hide();
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.errorModal.show();
    }

    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const files = fileInput.files;

        if (files.length === 0) {
            this.showError('Please select at least one PDF file to upload.');
            return;
        }

        this.showLoading('Uploading Documents...', 'Parsing PDF content and performing AI classification');

        try {
            const uploadPromises = Array.from(files).map(file => this.uploadSingleFile(file));
            await Promise.all(uploadPromises);
            
            // Refresh documents list
            await this.loadDocuments();
            
            // Clear file input
            fileInput.value = '';
            this.updateUploadButton(0);
            
            this.hideLoading();
            this.showSuccessToast(`Successfully uploaded ${files.length} document(s)`);
            
        } catch (error) {
            this.hideLoading();
            this.showError(`Upload failed: ${error.message}`);
        }
    }

    async uploadSingleFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.apiBase}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Failed to upload ${file.name}`);
        }

        return await response.json();
    }

    async loadDocuments() {
        try {
            const documents = await this.apiCall('/documents');
            this.documents = documents;
            this.renderDocuments();
            this.updateComparisonSelects();
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.showError('Failed to load documents. Please refresh the page.');
        }
    }

    renderDocuments() {
        const container = document.getElementById('documentsList');
        
        if (this.documents.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-folder-open fa-2x mb-2"></i>
                    <p>No documents uploaded yet</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.documents.map(doc => `
            <div class="list-group-item document-item" data-doc-id="${doc.document_id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${this.truncateText(doc.filename, 30)}</h6>
                        <p class="mb-1 text-muted small">${doc.chunk_count} chunks</p>
                        <div class="d-flex gap-1">
                            <span class="document-badge domain-${doc.domain}">${doc.domain}</span>
                            <span class="document-badge bg-light text-dark">${doc.document_type}</span>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="confidence-score small text-muted">
                            ${Math.round(doc.classification_confidence * 100)}% confidence
                        </div>
                        <button class="btn btn-sm btn-outline-danger mt-1" onclick="ragSystem.deleteDocument('${doc.document_id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers for selection
        container.querySelectorAll('.document-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('button')) {
                    this.toggleDocumentSelection(item.dataset.docId);
                }
            });
        });
    }

    toggleDocumentSelection(docId) {
        const item = document.querySelector(`[data-doc-id="${docId}"]`);
        
        if (this.selectedDocuments.has(docId)) {
            this.selectedDocuments.delete(docId);
            item.classList.remove('selected');
        } else {
            this.selectedDocuments.add(docId);
            item.classList.add('selected');
        }
    }

    updateComparisonSelects() {
        const select1 = document.getElementById('compareDoc1');
        const select2 = document.getElementById('compareDoc2');
        
        const options = this.documents.map(doc => 
            `<option value="${doc.document_id}">${this.truncateText(doc.filename, 40)}</option>`
        ).join('');
        
        select1.innerHTML = '<option value="">Select first document...</option>' + options;
        select2.innerHTML = '<option value="">Select second document...</option>' + options;
    }

    async handleQuery() {
        const query = document.getElementById('queryInput').value.trim();
        const domain = document.getElementById('domainFilter').value;

        if (!query) {
            this.showError('Please enter a query.');
            return;
        }

        this.showLoading('Processing Query...', 'Using AI agents for intelligent document retrieval and analysis');

        try {
            const response = await this.apiCall('/query', {
                method: 'POST',
                body: JSON.stringify({
                    query: query,
                    domain_filter: domain || null,
                    top_k: 10
                })
            });

            this.hideLoading();
            this.displayQueryResult(response);
            
        } catch (error) {
            this.hideLoading();
            this.showError(`Query failed: ${error.message}`);
        }
    }

    async handleComparison() {
        const doc1 = document.getElementById('compareDoc1').value;
        const doc2 = document.getElementById('compareDoc2').value;
        const comparisonType = document.getElementById('comparisonType').value;
        const focusAreas = document.getElementById('focusAreas').value.trim();

        if (!doc1 || !doc2) {
            this.showError('Please select two documents to compare.');
            return;
        }

        if (doc1 === doc2) {
            this.showError('Please select two different documents to compare.');
            return;
        }

        this.showLoading('Comparing Documents...', 'Performing deep comparative analysis using AI agents');

        try {
            const response = await this.apiCall('/compare', {
                method: 'POST',
                body: JSON.stringify({
                    document_ids: [doc1, doc2],
                    comparison_type: comparisonType,
                    focus_areas: focusAreas ? focusAreas.split(',').map(s => s.trim()) : null
                })
            });

            this.hideLoading();
            this.displayComparisonResult(response);
            
        } catch (error) {
            this.hideLoading();
            this.showError(`Comparison failed: ${error.message}`);
        }
    }

    displayQueryResult(result) {
        const container = document.getElementById('resultsContent');
        
        const html = `
            <div class="result-card query-result p-4 fade-in">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="mb-0">
                        <i class="fas fa-search text-success me-2"></i>Query Result
                    </h5>
                    <div class="text-end">
                        <div class="confidence-bar mb-1" style="width: 100px;">
                            <div class="confidence-indicator" style="width: ${result.confidence * 100}%"></div>
                        </div>
                        <small class="text-muted">${Math.round(result.confidence * 100)}% confidence</small>
                    </div>
                </div>
                
                <div class="answer-section mb-4">
                    <h6 class="text-muted mb-2">Answer</h6>
                    <div class="answer-text">${this.formatText(result.answer)}</div>
                </div>
                
                ${result.sources.length > 0 ? `
                    <div class="sources-section mb-4">
                        <h6 class="text-muted mb-2">Sources</h6>
                        <div class="sources-list">
                            ${result.sources.map(source => `
                                <a href="#" class="source-link">
                                    <i class="fas fa-file-pdf me-1"></i>
                                    ${source.filename} (Page ${source.page})
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${result.related_concepts.length > 0 ? `
                    <div class="concepts-section mb-4">
                        <h6 class="text-muted mb-2">Related Concepts</h6>
                        <div class="concept-tags">
                            ${result.related_concepts.map(concept => `
                                <span class="badge bg-primary me-1 mb-1">${concept}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${result.reasoning_steps.length > 0 ? `
                    <div class="reasoning-section">
                        <h6 class="text-muted mb-2">
                            <i class="fas fa-brain me-1"></i>AI Reasoning Process
                        </h6>
                        <div class="reasoning-steps">
                            ${result.reasoning_steps.map((step, index) => `
                                <div class="reasoning-step">
                                    <div class="step-number">${index + 1}</div>
                                    <div class="step-text">${step}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        container.innerHTML = html;
    }

    displayComparisonResult(result) {
        const container = document.getElementById('resultsContent');
        
        const html = `
            <div class="result-card comparison-result p-4 fade-in">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <h5 class="mb-0">
                        <i class="fas fa-balance-scale text-warning me-2"></i>Comparison Analysis
                    </h5>
                    <div class="text-end">
                        <div class="confidence-bar mb-1" style="width: 100px;">
                            <div class="confidence-indicator" style="width: ${result.confidence * 100}%"></div>
                        </div>
                        <small class="text-muted">${Math.round(result.confidence * 100)}% confidence</small>
                    </div>
                </div>
                
                <div class="comparison-matrix">
                    ${result.similarities.length > 0 ? `
                        <div class="comparison-section">
                            <div class="section-title">
                                <i class="fas fa-check-circle text-success"></i>
                                Key Similarities (${result.similarities.length})
                            </div>
                            ${result.similarities.map(similarity => `
                                <div class="similarity-item">
                                    <i class="fas fa-check me-2 text-success"></i>
                                    ${similarity}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${result.differences.length > 0 ? `
                        <div class="comparison-section">
                            <div class="section-title">
                                <i class="fas fa-times-circle text-danger"></i>
                                Key Differences (${result.differences.length})
                            </div>
                            ${result.differences.map(difference => `
                                <div class="difference-item">
                                    <i class="fas fa-times me-2 text-danger"></i>
                                    ${difference}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="comparison-section">
                        <div class="section-title">
                            <i class="fas fa-lightbulb text-info"></i>
                            Detailed Analysis
                        </div>
                        <div class="analysis-text">
                            ${this.formatText(result.insights)}
                        </div>
                    </div>
                </div>
                
                ${result.reasoning_steps.length > 0 ? `
                    <div class="reasoning-section mt-4">
                        <h6 class="text-muted mb-2">
                            <i class="fas fa-brain me-1"></i>Analysis Process
                        </h6>
                        <div class="reasoning-steps">
                            ${result.reasoning_steps.map((step, index) => `
                                <div class="reasoning-step">
                                    <div class="step-number">${index + 1}</div>
                                    <div class="step-text">${step}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        container.innerHTML = html;
    }

    async deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
            return;
        }

        try {
            await this.apiCall(`/documents/${docId}`, { method: 'DELETE' });
            await this.loadDocuments();
            this.showSuccessToast('Document deleted successfully');
        } catch (error) {
            this.showError(`Failed to delete document: ${error.message}`);
        }
    }

    clearResults() {
        const container = document.getElementById('resultsContent');
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-lightbulb fa-3x mb-3"></i>
                <h5>Ready for Analysis</h5>
                <p>Upload documents and start querying to see intelligent insights</p>
            </div>
        `;
    }

    formatText(text) {
        if (!text) return '';
        
        // Convert line breaks to HTML
        return text.replace(/\n/g, '<br>');
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    showSuccessToast(message) {
        // Simple success indication - could be enhanced with toast library
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragSystem = new RAGSystemUI();
});

// Utility functions for external use
window.RAGUtils = {
    formatFileSize: (bytes) => {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },
    
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },
    
    downloadText: (text, filename) => {
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    }
};
