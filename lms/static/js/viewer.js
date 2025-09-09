/**
 * PDF viewer using PDF.js with enhanced security
 */
function loadPDF(pdfUrl) {
    console.log('Attempting to load PDF:', pdfUrl);
    
    // Check if PDF.js is loaded
    if (typeof window['pdfjs-dist/build/pdf'] === 'undefined') {
        console.error('PDF.js library not loaded');
        alert('PDF viewer is not available. Please try again later.');
        return;
    }
    
    const pdfjsLib = window['pdfjs-dist/build/pdf'];
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.worker.min.js';

    // Validate file type
    if (!pdfUrl || !pdfUrl.toLowerCase().endsWith('.pdf')) {
        console.error('Invalid file type for PDF viewer:', pdfUrl);
        alert('This file is not a PDF. Please download it instead.');
        return;
    }

    let pdfDoc = null,
        pageNum = 1,
        pageRendering = false,
        pageNumPending = null,
        scale = 1.5,
        canvas = document.getElementById('pdf-canvas');

    // Check if canvas element exists
    if (!canvas) {
        console.error('PDF canvas element not found');
        return;
    }

    const ctx = canvas.getContext('2d');

    // Security measures
    const disableSecurityMeasures = function() {
        // Disable right-click context menu
        canvas.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
        
        // Disable drag events
        canvas.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
        });
        
        // Disable text selection
        canvas.style.userSelect = 'none';
        canvas.style.webkitUserSelect = 'none';
        canvas.style.MozUserSelect = 'none';
        canvas.style.msUserSelect = 'none';
    };

    function renderPage(num) {
        if (!pdfDoc) {
            console.error('No PDF document loaded');
            return;
        }
        
        pageRendering = true;
        
        // Get the specified page
        pdfDoc.getPage(num).then(function(page) {
            // Set scale based on device pixel ratio for better rendering
            const deviceScale = window.devicePixelRatio || 1;
            const viewport = page.getViewport({ scale: scale * deviceScale });
            
            // Set canvas dimensions
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            // Scale context for high DPI displays
            ctx.setTransform(deviceScale, 0, 0, deviceScale, 0, 0);

            const renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };
            
            // Render the page
            const renderTask = page.render(renderContext);
            
            renderTask.promise.then(function() {
                pageRendering = false;
                // Update page info
                updatePageInfo();
                
                // If there's a pending render, do it
                if (pageNumPending !== null) {
                    renderPage(pageNumPending);
                    pageNumPending = null;
                }
            }).catch(function(error) {
                console.error('Page render error:', error);
                alert('Failed to render PDF page: ' + (error.message || 'Unknown error'));
            });
        }).catch(function(error) {
            console.error('Get page error:', error);
            alert('Failed to get PDF page: ' + (error.message || 'Unknown error'));
        });
    }

    function updatePageInfo() {
        const pageInfo = document.getElementById('page-info');
        if (pageInfo && pdfDoc) {
            pageInfo.textContent = `Page ${pageNum} of ${pdfDoc.numPages}`;
        }
    }

    function queueRenderPage(num) {
        if (pageRendering) {
            pageNumPending = num;
        } else {
            renderPage(num);
        }
    }

    // Navigation event listeners
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    
    if (prevButton) {
        prevButton.addEventListener('click', function() {
            if (pageNum <= 1) return;
            pageNum--;
            queueRenderPage(pageNum);
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            if (!pdfDoc) return;
            if (pageNum >= pdfDoc.numPages) return;
            pageNum++;
            queueRenderPage(pageNum);
        });
    }

    // Fetch PDF with proper error handling
    fetch(pdfUrl, { 
        method: 'HEAD',
        mode: 'cors'
    })
    .then(response => {
        console.log('HEAD response:', response.status, response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Unable to access PDF`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/pdf')) {
            throw new Error('File is not a valid PDF');
        }
        
        // Load the PDF document
        return pdfjsLib.getDocument({
            url: pdfUrl,
            withCredentials: false,
            httpHeaders: {
                'Accept': 'application/pdf'
            }
        }).promise;
    })
    .then(function(pdfDoc_) {
        pdfDoc = pdfDoc_;
        updatePageInfo();
        renderPage(pageNum);
        console.log('PDF loaded successfully:', pdfUrl);
        
        // Enable navigation buttons
        if (prevButton) prevButton.disabled = false;
        if (nextButton) nextButton.disabled = false;
        
        // Apply security measures after successful load
        disableSecurityMeasures();
    })
    .catch(function(error) {
        console.error('PDF load error:', error, 'URL:', pdfUrl);
        
        // Provide user-friendly error message
        let errorMessage = 'Failed to load PDF';
        if (error.message) {
            errorMessage += ': ' + error.message;
        } else if (error.name === 'InvalidPDFException') {
            errorMessage = 'The PDF file is invalid or corrupted.';
        } else if (error.name === 'MissingPDFException') {
            errorMessage = 'The PDF file is missing.';
        } else if (error.name === 'UnexpectedResponseException') {
            errorMessage = 'Server returned an unexpected response.';
        }
        
        alert(errorMessage);
        
        // Update page info with error message
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            pageInfo.textContent = 'Failed to load PDF';
        }
    });
}

// Initialize the viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check for PDF canvas and initialize if present
    const canvas = document.getElementById('pdf-canvas');
    if (canvas && typeof loadPDF === 'function') {
        console.log('PDF viewer ready');
    }
});