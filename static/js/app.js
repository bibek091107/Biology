/**
 * Bioinformatics Toolkit - Frontend JavaScript (Advanced Version)
 * Student-friendly code with detailed comments
 */

// Global variables to store current analysis results
let currentDNAAnalysis = null;
let currentAlignmentResult = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

// Wait for DOM to be fully loaded before running code
document.addEventListener('DOMContentLoaded', function() {
    console.log('DNA Toolkit initialized');
    
    initNavigation();
    initDNAAnalyzer();
    initSequenceAlignment();
    initHistory();
    
    updateHistoryBadge();
});

/**
 * Navigation System
 * Handles switching between different pages/features
 */
function showPage(pageName) {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    
    navItems.forEach(nav => nav.classList.remove('active'));
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById(pageName);
    const navItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    
    if (targetPage) {
        targetPage.classList.add('active');
    }
    if (navItem) {
        navItem.classList.add('active');
    }
    
    if (pageName === 'history') {
        loadHistory();
    }
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const featureCards = document.querySelectorAll('.feature-card');

    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const pageName = this.getAttribute('data-page');
            showPage(pageName);
        });
    });

    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            const goto = this.getAttribute('data-goto');
            const navItem = document.querySelector(`.nav-item[data-page="${goto}"]`);
            if (navItem) {
                navItem.click();
            }
        });
    });
}

// ============================================================================
// DNA ANALYZER
// ============================================================================

function initDNAAnalyzer() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const saveResultBtn = document.getElementById('save-result-btn');
    
    analyzeBtn.addEventListener('click', analyzeDNA);
    
    // PDF download button
    downloadPdfBtn.addEventListener('click', downloadCurrentPDF);
    
    // Save result button
    saveResultBtn.addEventListener('click', saveCurrentResult);
}

async function analyzeDNA() {
    const sequence = document.getElementById('dna-sequence').value.trim();
    
    if (!sequence) {
        showToast('Please enter a DNA sequence', 'error');
        return;
    }
    
    const analyzeBtn = document.getElementById('analyze-btn');
    analyzeBtn.textContent = 'Analyzing...';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch('/api/dna/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sequence: sequence })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Analysis failed', 'error');
            return;
        }
        
        // Store result globally for PDF/save
        currentDNAAnalysis = data;
        
        displayDNAResults(data);
        
        // Enable action buttons
        document.getElementById('download-pdf-btn').disabled = false;
        document.getElementById('save-result-btn').disabled = false;
        
        showToast('Analysis complete!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to connect to server', 'error');
    } finally {
        analyzeBtn.textContent = 'Analyze Sequence';
        analyzeBtn.disabled = false;
    }
}

function displayDNAResults(data) {
    const resultsSection = document.getElementById('dna-results');
    
    document.getElementById('seq-length').textContent = data.length + ' bp';
    document.getElementById('gc-content').textContent = data.gc_content + '%';
    document.getElementById('at-content').textContent = data.at_content + '%';
    document.getElementById('mol-weight').textContent = data.molecular_weight.toFixed(2) + ' Da';
    document.getElementById('rev-comp').textContent = data.reverse_complement;
    document.getElementById('rna-seq').textContent = data.rna_sequence;
    document.getElementById('protein-seq').textContent = data.protein_sequence;
    
    const baseCompDiv = document.getElementById('base-comp');
    baseCompDiv.innerHTML = '';
    for (const [base, count] of Object.entries(data.base_composition)) {
        const span = document.createElement('span');
        span.textContent = `${base}: ${count}`;
        baseCompDiv.appendChild(span);
    }
    
    resultsSection.classList.remove('hidden');
}

// ============================================================================
// SEQUENCE ALIGNMENT
// ============================================================================

function initSequenceAlignment() {
    const alignBtn = document.getElementById('align-btn');
    const pdfBtn = document.getElementById('align-pdf-btn');
    const saveBtn = document.getElementById('align-save-btn');
    
    alignBtn.addEventListener('click', alignSequences);
    pdfBtn.addEventListener('click', downloadAlignmentPDF);
    saveBtn.addEventListener('click', saveAlignmentResult);
}

async function alignSequences() {
    const seq1 = document.getElementById('seq1').value.trim();
    const seq2 = document.getElementById('seq2').value.trim();
    
    if (!seq1 || !seq2) {
        showToast('Please enter both sequences', 'error');
        return;
    }
    
    const alignBtn = document.getElementById('align-btn');
    alignBtn.textContent = 'Aligning...';
    alignBtn.disabled = true;
    
    try {
        const response = await fetch('/api/align', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sequence1: seq1, sequence2: seq2 })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Alignment failed', 'error');
            return;
        }
        
        // Store result globally
        currentAlignmentResult = data;
        
        displayAlignmentResults(data);
        
        // Enable action buttons
        document.getElementById('align-pdf-btn').disabled = false;
        document.getElementById('align-save-btn').disabled = false;
        
        showToast('Alignment complete!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to connect to server', 'error');
    } finally {
        alignBtn.textContent = 'Align Sequences';
        alignBtn.disabled = false;
    }
}

function displayAlignmentResults(data) {
    const resultsSection = document.getElementById('align-results');
    
    document.getElementById('align-seq1').textContent = data.sequence1;
    document.getElementById('align-seq2').textContent = data.sequence2;
    document.getElementById('identity').textContent = data.identity + '%';
    document.getElementById('matches').textContent = data.matches;
    document.getElementById('mismatches').textContent = data.mismatches;
    document.getElementById('align-length').textContent = data.alignment_length + ' bp';
    
    resultsSection.classList.remove('hidden');
}

// ============================================================================
// HISTORY MANAGEMENT
// ============================================================================

function initHistory() {
    const clearBtn = document.getElementById('clear-history-btn');
    clearBtn.addEventListener('click', clearAllHistory);
}

async function loadHistory() {
    const historyList = document.getElementById('history-list');
    const historyEmpty = document.getElementById('history-empty');
    
    historyList.innerHTML = '<div class="loading">Loading history...</div>';
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load history');
        }
        
        if (data.history.length === 0) {
            historyList.classList.add('hidden');
            historyEmpty.classList.remove('hidden');
        } else {
            historyList.classList.remove('hidden');
            historyEmpty.classList.add('hidden');
            displayHistory(data.history);
        }
        
        updateHistoryBadge();
        
    } catch (error) {
        console.error('Error:', error);
        historyList.innerHTML = '<p class="error">Failed to load history</p>';
    }
}

function displayHistory(history) {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    history.forEach(entry => {
        const entryCard = document.createElement('div');
        entryCard.className = 'history-entry';
        
        const typeLabel = entry.type === 'dna_analysis' ? 'DNA Analysis' : 'Sequence Alignment';
        const summary = entry.type === 'dna_analysis' 
            ? `GC Content: ${entry.data.gc_content}%, Length: ${entry.data.length} bp`
            : `Identity: ${entry.data.identity}%, Matches: ${entry.data.matches}`;
        
        entryCard.innerHTML = `
            <div class="history-entry-header">
                <div>
                    <h4>${typeLabel}</h4>
                    <span class="timestamp">${entry.timestamp}</span>
                </div>
            </div>
            <p class="history-entry-summary">${summary}</p>
            <div class="history-entry-actions">
                <button class="btn-view" onclick="viewHistoryDetail('${entry.id}')">View Details</button>
                <button class="btn-delete" onclick="deleteHistoryEntry('${entry.id}')">Delete</button>
            </div>
        `;
        
        historyList.appendChild(entryCard);
    });
}

async function viewHistoryDetail(entryId) {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        const entry = data.history.find(h => h.id === entryId);
        if (!entry) {
            showToast('Entry not found', 'error');
            return;
        }
        
        // Store current entry ID for PDF download
        window.currentHistoryEntry = entry;
        
        // Build modal content
        let content = '';
        
        if (entry.type === 'dna_analysis') {
            content = `
                <div class="history-detail">
                    <h4>Input Sequence</h4>
                    <code style="display:block;word-break:break-all;background:var(--bg-dark);padding:12px;border-radius:6px;margin-bottom:16px;">${entry.data.sequence}</code>
                    
                    <h4>Analysis Results</h4>
                    <div class="results-grid">
                        <div class="result-card">
                            <h4>Length</h4>
                            <p>${entry.data.length} bp</p>
                        </div>
                        <div class="result-card">
                            <h4>GC Content</h4>
                            <p>${entry.data.gc_content}%</p>
                        </div>
                        <div class="result-card">
                            <h4>AT Content</h4>
                            <p>${entry.data.at_content}%</p>
                        </div>
                        <div class="result-card">
                            <h4>Molecular Weight</h4>
                            <p>${entry.data.molecular_weight} Da</p>
                        </div>
                    </div>
                    
                    <h4 style="margin-top:20px;">Reverse Complement</h4>
                    <code style="display:block;word-break:break-all;background:var(--bg-dark);padding:12px;border-radius:6px;">${entry.data.reverse_complement}</code>
                    
                    <h4 style="margin-top:20px;">Protein Translation</h4>
                    <code style="display:block;word-break:break-all;background:var(--bg-dark);padding:12px;border-radius:6px;">${entry.data.protein_sequence}</code>
                </div>
            `;
        } else {
            content = `
                <div class="history-detail">
                    <h4>Sequences</h4>
                    <p><strong>Sequence 1:</strong></p>
                    <code style="display:block;word-break:break-all;background:var(--bg-dark);padding:12px;border-radius:6px;margin-bottom:12px;">${entry.data.sequence1}</code>
                    <p><strong>Sequence 2:</strong></p>
                    <code style="display:block;word-break:break-all;background:var(--bg-dark);padding:12px;border-radius:6px;margin-bottom:16px;">${entry.data.sequence2}</code>
                    
                    <h4>Alignment Results</h4>
                    <div class="results-grid">
                        <div class="result-card">
                            <h4>Identity</h4>
                            <p>${entry.data.identity}%</p>
                        </div>
                        <div class="result-card">
                            <h4>Matches</h4>
                            <p>${entry.data.matches}</p>
                        </div>
                        <div class="result-card">
                            <h4>Mismatches</h4>
                            <p>${entry.data.mismatches}</p>
                        </div>
                        <div class="result-card">
                            <h4>Length</h4>
                            <p>${entry.data.alignment_length} bp</p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        document.getElementById('modal-title').textContent = 
            entry.type === 'dna_analysis' ? 'DNA Analysis Details' : 'Alignment Details';
        document.getElementById('modal-body').innerHTML = content;
        
        // Set up PDF download button
        document.getElementById('modal-download-btn').onclick = () => downloadHistoryPDF(entry);
        
        openModal();
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to load details', 'error');
    }
}

async function deleteHistoryEntry(entryId) {
    if (!confirm('Are you sure you want to delete this entry?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${entryId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete');
        }
        
        showToast('Entry deleted', 'success');
        loadHistory();
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to delete entry', 'error');
    }
}

async function clearAllHistory() {
    if (!confirm('Are you sure you want to clear all history? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/history/clear', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to clear history');
        }
        
        showToast('History cleared', 'success');
        loadHistory();
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to clear history', 'error');
    }
}

function updateHistoryBadge() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('history-badge');
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error updating badge:', error);
        });
}

// ============================================================================
// PDF DOWNLOAD
// ============================================================================

async function downloadCurrentPDF() {
    if (!currentDNAAnalysis) {
        showToast('No analysis to download', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/download/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'dna_analysis',
                data: currentDNAAnalysis
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate PDF');
        }
        
        // Download the PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `biotoolkit_dna_analysis_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('PDF downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to generate PDF', 'error');
    } finally {
        showLoading(false);
    }
}

async function downloadAlignmentPDF() {
    if (!currentAlignmentResult) {
        showToast('No alignment to download', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/download/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'alignment',
                data: currentAlignmentResult
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate PDF');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `biotoolkit_alignment_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('PDF downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to generate PDF', 'error');
    } finally {
        showLoading(false);
    }
}

async function downloadHistoryPDF(entry) {
    showLoading(true);
    closeModal();
    
    try {
        const response = await fetch('/api/download/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: entry.type,
                data: entry.data
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate PDF');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `biotoolkit_${entry.type}_${entry.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('PDF downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to generate PDF', 'error');
    } finally {
        showLoading(false);
    }
}

// ============================================================================
// SAVE RESULTS
// ============================================================================

async function saveCurrentResult() {
    if (!currentDNAAnalysis) {
        showToast('No analysis to save', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'dna_analysis',
                data: currentDNAAnalysis
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to save');
        }
        
        showToast('Result saved to history!', 'success');
        updateHistoryBadge();
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to save result', 'error');
    }
}

async function saveAlignmentResult() {
    if (!currentAlignmentResult) {
        showToast('No alignment to save', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'alignment',
                data: currentAlignmentResult
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to save');
        }
        
        showToast('Result saved to history!', 'success');
        updateHistoryBadge();
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to save result', 'error');
    }
}

// ============================================================================
// MODAL
// ============================================================================

function openModal() {
    document.getElementById('history-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('history-modal').classList.add('hidden');
}

// Close modal when clicking overlay
document.querySelector('.modal-overlay')?.addEventListener('click', closeModal);

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================

function showToast(message, type = 'error') {
    const toast = document.getElementById(type + '-toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// ============================================================================
// LOADING OVERLAY
// ============================================================================

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}
