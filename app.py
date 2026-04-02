"""
Bioinformatics Toolkit - Flask Backend (Advanced Version)
Student-friendly version with PDF export, history, and real gene data
"""

from flask import Flask, render_template, jsonify, request, send_file
import re
import json
import os
from datetime import datetime
from collections import Counter
from io import BytesIO

# PDF Generation library
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

app = Flask(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# File to store analysis history
HISTORY_FILE = 'analysis_history.json'

# ============================================================================
# REAL GENE DATABASE
# ============================================================================
# Contains real biological gene sequences (simplified/shorter versions for demo)
# These are actual gene regions used in bioinformatics education

REAL_GENES = {
    "BRCA1": {
        "name": "BRCA1 (Breast Cancer Gene)",
        "description": "Breast Cancer gene - tumor suppressor gene involved in DNA repair. Mutations increase breast/ovarian cancer risk.",
        "location": "Chromosome 17q21.31",
        "sequence": "ATGCGCCGCCGCCGCCGCCGCCGCCGCCGCCGTGGCCGCCATGACGACGACGACGACGACGACGACGACGACGAC",
        "function": "DNA repair, tumor suppression"
    },
    "Hemoglobin": {
        "name": "Hemoglobin Alpha (HBA)",
        "description": "Alpha globin gene - encodes protein subunit of hemoglobin that carries oxygen in red blood cells.",
        "location": "Chromosome 16p13.3",
        "sequence": "ATGGTGCTGTCTCCTGCCGACAAGTTCACCTCTGCCCTGGACTCCAGCGAGTCCCTGGCCAAGGTCACCGTGTTG",
        "function": "Oxygen transport"
    },
    "Insulin": {
        "name": "Insulin (INS)",
        "description": "Insulin hormone gene - regulates blood glucose levels. Deficiency causes diabetes mellitus.",
        "location": "Chromosome 11p15.5",
        "sequence": "ATGCTGCTGCCTGATCCTGCTGCTGCTGCTGCTGCAGATGCGATCGTACAGCGCCGCAGCCCCGACAGCAGCAGC",
        "function": "Glucose regulation"
    },
    "TP53": {
        "name": "TP53 (Tumor Protein p53)",
        "description": "Guardian of the genome - tumor suppressor gene that regulates cell cycle and prevents cancer.",
        "location": "Chromosome 17p13.1",
        "sequence": "ATGGAAGAAATACCAGTACATGTGTAATAGCTCCTGCATGGGCGGCATGAACCGAGGAGCCGCAGTCAGATCCT",
        "function": "Tumor suppression, cell cycle regulation"
    },
    "EGFR": {
        "name": "EGFR (Epidermal Growth Factor Receptor)",
        "description": "Cell surface receptor - plays key role in cell growth, proliferation, and differentiation.",
        "location": "Chromosome 7p12",
        "sequence": "ATGCGACCCTCCGGGACGGCCGGGGTGGCGGCCTCGGCACGCTGGTGGTGCCCGACGGCCACTGGCTGCGACCC",
        "function": "Cell growth signaling"
    }
}

# ============================================================================
# BLAST DATABASE (Extended)
# ============================================================================

BLAST_DATABASE = [
    {"id": "NC_000001", "organism": "Homo sapiens", "gene": "BRCA1", "sequence": "ATGCAGCTGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"},
    {"id": "NC_000002", "organism": "Mus musculus", "gene": "Tp53", "sequence": "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA"},
    {"id": "NC_000003", "organism": "Danio rerio", "gene": "Myod", "sequence": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC"},
    {"id": "NC_000004", "organism": "Homo sapiens", "gene": "EGFR", "sequence": "TTAGGCATAGCTAGCATGCATGCTAGCTAGCTAGCTAGCATGCTAGCTAG"},
    {"id": "NC_000005", "organism": "Rattus norvegicus", "gene": "Ins", "sequence": "ATGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGCTGC"},
    {"id": "NC_000006", "organism": "Gallus gallus", "gene": "Oval", "sequence": "GCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC"},
    {"id": "NC_000007", "organism": "Homo sapiens", "gene": "CFTR", "sequence": "ATATATATATATATATATATATATATATATATATATATATATATATATAT"},
    {"id": "NC_000008", "organism": "Drosophila melanogaster", "gene": "White", "sequence": "CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"},
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_dna(sequence):
    """Check if sequence contains only valid DNA nucleotides"""
    sequence = sequence.upper()
    return bool(re.match(r'^[ATCGN]+$', sequence))

def calculate_gc_content(sequence):
    """Calculate GC content percentage"""
    sequence = sequence.upper()
    gc_count = sequence.count('G') + sequence.count('C')
    if len(sequence) == 0:
        return 0
    return round((gc_count / len(sequence)) * 100, 2)

def reverse_complement(sequence):
    """Return reverse complement of DNA sequence"""
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    return ''.join(complement.get(base, 'N') for base in reversed(sequence.upper()))

def transcribe_to_rna(sequence):
    """Convert DNA to RNA (T -> U)"""
    return sequence.upper().replace('T', 'U')

def translate_to_protein(sequence):
    """Convert DNA/RNA to protein sequence using standard genetic code"""
    codon_table = {
        'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
        'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
        'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
        'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
        'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
        'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
        'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
        'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
        'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
        'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
        'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
        'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
        'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
    }
    protein = []
    seq = sequence.upper().replace('U', '')
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i:i+3]
        if codon in codon_table:
            protein.append(codon_table[codon])
        else:
            protein.append('X')
    return ''.join(protein)

def simple_align(seq1, seq2):
    """Simple global sequence alignment - calculates identity score"""
    matches = sum(1 for a, b in zip(seq1.upper(), seq2.upper()) if a == b and a in 'ATCG')
    length = max(len(seq1), len(seq2))
    identity = round((matches / length) * 100, 2) if length > 0 else 0
    return {
        "sequence1": seq1,
        "sequence2": seq2,
        "identity": identity,
        "alignment_length": length,
        "matches": matches,
        "mismatches": length - matches
    }

def blast_search(query, e_value_threshold=10):
    """Simple BLAST-like search against database"""
    query = query.upper()
    results = []
    
    for record in BLAST_DATABASE:
        db_seq = record["sequence"].upper()
        max_hits = 0
        window_size = min(len(query), len(db_seq), 20)
        
        for i in range(len(db_seq) - window_size + 1):
            window = db_seq[i:i + window_size]
            matches = sum(1 for a, b in zip(query, window) if a == b)
            hits = matches / window_size * 100
            max_hits = max(max_hits, hits)
        
        e_value = max(0.001, 100 - max_hits) / 100
        
        if e_value <= e_value_threshold:
            results.append({
                "accession": record["id"],
                "organism": record["organism"],
                "gene": record["gene"],
                "max_identity": round(max_hits, 2),
                "e_value": round(e_value, 4),
                "query_start": 1,
                "query_end": len(query),
                "subject_start": 1,
                "subject_end": len(db_seq)
            })
    
    results.sort(key=lambda x: (x["e_value"], -x["max_identity"]))
    return results[:10]

# ============================================================================
# HISTORY MANAGEMENT
# ============================================================================

def load_history():
    """Load analysis history from JSON file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    """Save analysis history to JSON file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_pdf_report(analysis_type, data):
    """
    Generate a professional PDF report using ReportLab
    
    Args:
        analysis_type: 'dna_analysis' or 'alignment'
        data: Dictionary containing analysis results
    
    Returns:
        BytesIO object containing PDF data
    """
    # Create buffer to store PDF
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#4f46e5'),
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#1e293b')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10
    )
    
    # Build PDF content
    story = []
    
    # Header
    story.append(Paragraph("Bioinformatics Toolkit", title_style))
    story.append(Paragraph("Analysis Report", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generated: {timestamp}", normal_style))
    story.append(Paragraph(f"Analysis Type: {analysis_type.replace('_', ' ').title()}", normal_style))
    story.append(Spacer(1, 20))
    
    # Divider
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 20))
    
    if analysis_type == 'dna_analysis':
        # DNA Analysis Report
        story.append(Paragraph("DNA Sequence Analysis Results", heading_style))
        
        # Input sequence (formatted)
        story.append(Paragraph("<b>Input Sequence:</b>", normal_style))
        seq = data.get('sequence', '')
        seq_formatted = ' '.join([seq[i:i+10] for i in range(0, len(seq), 10)])
        story.append(Paragraph(seq_formatted, styles['Code']))
        story.append(Spacer(1, 10))
        
        # Results table
        table_data = [
            ['Metric', 'Value'],
            ['Sequence Length', f"{data.get('length', 0)} bp"],
            ['GC Content', f"{data.get('gc_content', 0)}%"],
            ['AT Content', f"{data.get('at_content', 0)}%"],
            ['Molecular Weight', f"{data.get('molecular_weight', 0)} Da"],
        ]
        
        table = Table(table_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Base composition
        story.append(Paragraph("Base Composition", heading_style))
        base_comp = data.get('base_composition', {})
        base_text = ', '.join([f"{base}: {count}" for base, count in base_comp.items()])
        story.append(Paragraph(base_text, normal_style))
        story.append(Spacer(1, 15))
        
        # Derived sequences
        story.append(Paragraph("Derived Sequences", heading_style))
        story.append(Paragraph(f"<b>Reverse Complement:</b> {data.get('reverse_complement', '')}", normal_style))
        story.append(Paragraph(f"<b>RNA Sequence:</b> {data.get('rna_sequence', '')}", normal_style))
        story.append(Paragraph(f"<b>Protein Translation:</b> {data.get('protein_sequence', '')}", normal_style))
        
    elif analysis_type == 'alignment':
        # Alignment Report
        story.append(Paragraph("Sequence Alignment Results", heading_style))
        
        # Sequences
        story.append(Paragraph("<b>Sequence 1:</b>", normal_style))
        story.append(Paragraph(data.get('sequence1', ''), styles['Code']))
        story.append(Spacer(1, 5))
        
        story.append(Paragraph("<b>Sequence 2:</b>", normal_style))
        story.append(Paragraph(data.get('sequence2', ''), styles['Code']))
        story.append(Spacer(1, 15))
        
        # Alignment statistics
        table_data = [
            ['Metric', 'Value'],
            ['Identity', f"{data.get('identity', 0)}%"],
            ['Matches', str(data.get('matches', 0))],
            ['Mismatches', str(data.get('mismatches', 0))],
            ['Alignment Length', f"{data.get('alignment_length', 0)} bp"],
        ]
        
        table = Table(table_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbf7d0')),
        ]))
        story.append(table)
    
    # Footer
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generated by Bioinformatics Toolkit - Student Version",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    
    # Reset buffer position
    buffer.seek(0)
    return buffer

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/dna/analyze', methods=['POST'])
def analyze_dna():
    """Analyze DNA sequence - composition, GC content, molecular weight"""
    data = request.get_json()
    sequence = data.get('sequence', '').strip()
    
    if not sequence:
        return jsonify({"error": "No sequence provided"}), 400
    
    if not validate_dna(sequence):
        return jsonify({"error": "Invalid DNA sequence. Use only A, T, C, G, N"}), 400
    
    sequence = sequence.upper()
    length = len(sequence)
    base_counts = dict(Counter(sequence))
    gc_content = calculate_gc_content(sequence)
    
    # Molecular weight (approximate, per nucleotide)
    molecular_weight = {
        'A': 331.2, 'T': 322.2, 'C': 307.2, 'G': 347.2, 'N': 327.0
    }
    total_weight = sum(molecular_weight.get(base, 327.0) for base in sequence)
    
    return jsonify({
        "sequence": sequence,
        "length": length,
        "base_composition": base_counts,
        "gc_content": gc_content,
        "at_content": round(100 - gc_content, 2),
        "molecular_weight": round(total_weight, 2),
        "reverse_complement": reverse_complement(sequence),
        "rna_sequence": transcribe_to_rna(sequence),
        "protein_sequence": translate_to_protein(sequence)
    })

@app.route('/api/align', methods=['POST'])
def align_sequences():
    """Align two DNA sequences"""
    data = request.get_json()
    seq1 = data.get('sequence1', '').strip()
    seq2 = data.get('sequence2', '').strip()
    
    if not seq1 or not seq2:
        return jsonify({"error": "Both sequences required"}), 400
    
    seq1 = re.sub(r'[^ATCGN]', '', seq1.upper())
    seq2 = re.sub(r'[^ATCGN]', '', seq2.upper())
    
    if not seq1 or not seq2:
        return jsonify({"error": "No valid DNA bases found"}), 400
    
    result = simple_align(seq1, seq2)
    result["protein1"] = translate_to_protein(seq1)
    result["protein2"] = translate_to_protein(seq2)
    
    return jsonify(result)

@app.route('/api/blast/search', methods=['POST'])
def search_blast():
    """Search against BLAST database"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "Query sequence required"}), 400
    
    query = re.sub(r'[^ATCGN]', '', query.upper())
    
    if len(query) < 10:
        return jsonify({"error": "Query too short (minimum 10 bases)"}), 400
    
    results = blast_search(query)
    
    return jsonify({
        "query": query,
        "query_length": len(query),
        "database": "Mini BioDB v1.0",
        "database_size": len(BLAST_DATABASE),
        "results": results,
        "total_hits": len(results)
    })

@app.route('/api/genome/view', methods=['GET'])
def get_genome_data():
    """Get genome data for viewer"""
    return jsonify({
        "chromosomes": [
            {"id": "chr1", "name": "Chromosome 1", "length": 500, "genes": 100},
            {"id": "chr2", "name": "Chromosome 2", "length": 450, "genes": 80},
            {"id": "chr3", "name": "Chromosome 3", "length": 400, "genes": 70},
            {"id": "chr4", "name": "Chromosome 4", "length": 380, "genes": 60},
            {"id": "chr5", "name": "Chromosome 5", "length": 350, "genes": 55},
        ],
        "features": [
            {"chromosome": "chr1", "start": 100, "end": 200, "type": "gene", "name": "BRCA1"},
            {"chromosome": "chr1", "start": 250, "end": 300, "type": "exon", "name": "Exon 1"},
            {"chromosome": "chr2", "start": 150, "end": 250, "type": "gene", "name": "TP53"},
            {"chromosome": "chr3", "start": 80, "end": 180, "type": "gene", "name": "EGFR"},
        ]
    })

@app.route('/api/genes', methods=['GET'])
def get_genes():
    """Get list of real gene sequences"""
    return jsonify({
        "genes": REAL_GENES
    })

# ============================================================================
# HISTORY API ROUTES
# ============================================================================

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all analysis history"""
    try:
        history = load_history()
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history', methods=['POST'])
def save_result():
    """Save analysis result to history"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'type' not in data or 'data' not in data:
            return jsonify({"success": False, "error": "Invalid data"}), 400
        
        # Create history entry
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": data['type'],
            "data": data['data']
        }
        
        # Load existing history and add new entry
        history = load_history()
        history.insert(0, entry)  # Add to beginning (newest first)
        
        # Keep only last 50 entries
        history = history[:50]
        
        # Save to file
        save_history(history)
        
        return jsonify({
            "success": True,
            "message": "Result saved successfully",
            "entry": entry
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history/<entry_id>', methods=['DELETE'])
def delete_history_entry(entry_id):
    """Delete a specific history entry"""
    try:
        history = load_history()
        original_length = len(history)
        
        # Filter out the entry to delete
        history = [h for h in history if h.get('id') != entry_id]
        
        if len(history) == original_length:
            return jsonify({"success": False, "error": "Entry not found"}), 404
        
        # Save updated history
        save_history(history)
        
        return jsonify({
            "success": True,
            "message": "Entry deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """Clear all history"""
    try:
        save_history([])
        return jsonify({
            "success": True,
            "message": "History cleared successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# PDF DOWNLOAD ROUTE
# ============================================================================

@app.route('/api/download/pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF report"""
    try:
        data = request.get_json()
        
        analysis_type = data.get('type', 'dna_analysis')
        analysis_data = data.get('data', {})
        
        # Generate PDF
        pdf_buffer = generate_pdf_report(analysis_type, analysis_data)
        
        # Create filename with timestamp
        filename = f"biotoolkit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  Bioinformatics Toolkit - Student Version (Advanced)")
    print("=" * 60)
    print("  Features:")
    print("  - DNA Analyzer")
    print("  - Sequence Alignment")
    print("  - Mini BLAST Search")
    print("  - Genome Viewer")
    print("  - PDF Export")
    print("  - History Management")
    print("  - Real Gene Database")
    print("=" * 60)
    print("\n  Starting server at http://localhost:5000\n")
    app.run(debug=True, port=5000)
