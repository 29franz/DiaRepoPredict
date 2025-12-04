// Load predictions history
function loadPredictionsHistory() {
    fetch('/get_predictions_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPredictionsHistory(data.history);
                document.getElementById('historyCount').textContent = data.total_count;
            } else {
                showError('Failed to load history: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading history:', error);
            showError('Failed to load predictions history');
        });
}

// Display predictions history in table
function displayPredictionsHistory(predictions) {
    const tableBody = document.getElementById('predictionsTableBody');
    const noPredictionsRow = document.getElementById('noPredictionsRow');
    
    if (!predictions || predictions.length === 0) {
        if (noPredictionsRow) {
            noPredictionsRow.style.display = '';
        }
        return;
    }
    
    // Hide "no predictions" row
    if (noPredictionsRow) {
        noPredictionsRow.style.display = 'none';
    }
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add each prediction to the table
    predictions.forEach(pred => {
        const row = document.createElement('tr');
        
        // Format features for display
        let featuresDisplay = '';
        let riskPercent = 'N/A';
        let predictionText = 'N/A';
        let isBatch = pred.type !== 'single';
        
        if (isBatch) {
            // For batch predictions
            const stats = pred.statistics || {};
            featuresDisplay = `<span class="badge bg-info">Batch: ${stats.total_records || pred.predictions.length} records</span>`;
            riskPercent = `${stats.high_risk_percentage || 'N/A'}% High Risk`;
            predictionText = `${stats.high_risk || 0} High, ${stats.low_risk || 0} Low`;
        } else {
            // For single predictions
            const input = pred.input_data || {};
            featuresDisplay = `
                <small>
                    <div>Glucose: ${input.Glucose || 'N/A'}</div>
                    <div>BMI: ${input.BMI || 'N/A'}</div>
                    <div>Age: ${input.Age || 'N/A'}</div>
                </small>
            `;
            
            // Extract risk percentage from prediction
            if (pred.predictions && pred.predictions.length > 0) {
                riskPercent = `${pred.predictions[0].probability || 'N/A'}%`;
                predictionText = pred.predictions[0].risk_level === 'High' ? 
                    '<span class="badge bg-danger">High Risk</span>' : 
                    '<span class="badge bg-success">Low Risk</span>';
            }
        }
        
        row.innerHTML = `
            <td>
                <span class="badge bg-secondary">${pred.id.substring(0, 6)}</span>
            </td>
            <td>
                <small>${pred.timestamp}</small>
            </td>
            <td>
                ${isBatch ? 
                    `<span class="badge bg-primary"><i class="fas fa-users me-1"></i> Batch</span>` : 
                    `<span class="badge bg-success"><i class="fas fa-user me-1"></i> Single</span>`}
            </td>
            <td>${featuresDisplay}</td>
            <td>
                <strong>${riskPercent}</strong>
            </td>
            <td>${predictionText}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary" onclick="downloadPrediction('${pred.id}')" 
                            title="Download CSV">
                        <i class="fas fa-download"></i>
                    </button>
                    ${isBatch ? `
                    <button class="btn btn-outline-info" onclick="viewBatchDetails('${pred.id}')" 
                            title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Download single prediction
function downloadPrediction(predictionId) {
    fetch(`/download_predictions/${predictionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed');
            }
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `prediction_${predictionId}.csv`;
            
            // Trigger download
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Show success message
            showSuccess('Download started!');
        })
        .catch(error => {
            console.error('Download error:', error);
            showError('Failed to download predictions');
        });
}

// View batch prediction details
let currentBatchId = null;

function viewBatchDetails(batchId) {
    currentBatchId = batchId;
    
    // Find the prediction in loaded history
    fetch('/get_predictions_history')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const prediction = data.history.find(p => p.id === batchId);
                if (prediction) {
                    displayBatchDetails(prediction);
                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('batchDetailsModal'));
                    modal.show();
                }
            }
        })
        .catch(error => {
            console.error('Error loading batch details:', error);
            showError('Failed to load batch details');
        });
}

// Display batch details in modal
function displayBatchDetails(prediction) {
    const contentDiv = document.getElementById('batchDetailsContent');
    const predictions = prediction.predictions || [];
    const stats = prediction.statistics || {};
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">Batch Information</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>ID:</strong> ${prediction.id}</p>
                        <p><strong>Timestamp:</strong> ${prediction.timestamp}</p>
                        <p><strong>Model:</strong> ${prediction.model_used}</p>
                        <p><strong>Type:</strong> ${prediction.type}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">Statistics</h6>
                    </div>
                    <div class="card-body">
                        <p><strong>Total Records:</strong> ${stats.total_records || predictions.length}</p>
                        <p><strong>High Risk:</strong> ${stats.high_risk || 'N/A'}</p>
                        <p><strong>Low Risk:</strong> ${stats.low_risk || 'N/A'}</p>
                        <p><strong>High Risk %:</strong> ${stats.high_risk_percentage || 'N/A'}%</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">Sample Predictions (First 10)</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Glucose</th>
                                <th>BMI</th>
                                <th>Age</th>
                                <th>Prediction</th>
                                <th>Probability</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    // Show first 10 predictions
    const samplePredictions = predictions.slice(0, 10);
    samplePredictions.forEach((pred, index) => {
        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${pred.Glucose || 'N/A'}</td>
                <td>${pred.BMI || 'N/A'}</td>
                <td>${pred.Age || 'N/A'}</td>
                <td>
                    ${pred.Risk_Level === 'High' ? 
                        '<span class="badge bg-danger">High Risk</span>' : 
                        '<span class="badge bg-success">Low Risk</span>'}
                </td>
                <td><strong>${pred.Probability || 'N/A'}</strong></td>
            </tr>
        `;
    });
    
    if (predictions.length > 10) {
        html += `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i>... and ${predictions.length - 10} more records</i>
                </td>
            </tr>
        `;
    }
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    contentDiv.innerHTML = html;
    
    // Set up download button
    document.getElementById('downloadBatchBtn').onclick = function() {
        downloadPrediction(prediction.id);
    };
}

// Download all predictions
document.getElementById('downloadAllBtn')?.addEventListener('click', function() {
    fetch('/download_all_predictions')
        .then(response => {
            if (!response.ok) {
                throw new Error('Download failed');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Create filename with timestamp
            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
            a.download = `all_predictions_${timestamp}.csv`;
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showSuccess('All predictions download started!');
        })
        .catch(error => {
            console.error('Download error:', error);
            showError('Failed to download all predictions');
        });
});

// Clear history
document.getElementById('clearHistoryBtn')?.addEventListener('click', function() {
    if (confirm('Are you sure you want to clear all prediction history? This action cannot be undone.')) {
        fetch('/clear_predictions_history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(data.message);
                loadPredictionsHistory(); // Reload history (will be empty)
            } else {
                showError('Failed to clear history: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Clear history error:', error);
            showError('Failed to clear history');
        });
    }
});

// Utility functions for showing messages
function showSuccess(message) {
    // Create a toast or alert
    const toast = document.createElement('div');
    toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Load history on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPredictionsHistory();
    
    // Refresh history every 30 seconds
    setInterval(loadPredictionsHistory, 30000);
});

// After making a single prediction, refresh history
// Add this to your existing single prediction success callback:
function onSinglePredictionSuccess(data) {
    // Your existing success handling code...
    
    // Then refresh history
    loadPredictionsHistory();
}

// After batch prediction (CSV upload), refresh history
function onBatchPredictionSuccess(data) {
    // Your existing batch success handling code...
    
    // Then refresh history
    loadPredictionsHistory();
}