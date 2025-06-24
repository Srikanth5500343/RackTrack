/**
 * JSON Visualizer
 * Provides interactive visualization of JSON data from CSV conversion
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the results page with the JSON visualizer
    const jsonContainer = document.getElementById('json-container');
    const jsonPreview = document.getElementById('json-preview');
    const toggleJsonView = document.getElementById('toggle-json-view');

    if (!jsonContainer || !jsonPreview || !toggleJsonView) return;

    // Toggle JSON view visibility
    toggleJsonView.addEventListener('change', function() {
        if (this.checked) {
            jsonContainer.classList.remove('d-none');
            fetchJsonData();
        } else {
            jsonContainer.classList.add('d-none');
        }
    });

    // Fetch JSON data from API
    function fetchJsonData() {
        jsonPreview.textContent = 'Loading JSON data...';

        fetch('/api/json-data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Format and display JSON
                displayJsonData(data);
            })
            .catch(error => {
                console.error('Error fetching JSON data:', error);
                jsonPreview.textContent = 'Error loading JSON data: ' + error.message;
                jsonPreview.classList.add('text-danger');
            });
    }

    // Display JSON data with syntax highlighting
    function displayJsonData(data) {
        // Format JSON with indentation for readability
        const prettyJson = JSON.stringify(data, null, 2);

        // Apply syntax highlighting (basic approach)
        const highlightedJson = prettyJson
            .replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>') // keys
            .replace(/"([^"]+)"/g, '<span class="json-string">"$1"</span>') // strings
            .replace(/\b(\d+\.?\d*)\b/g, '<span class="json-number">$1</span>') // numbers
            .replace(/\b(true|false|null)\b/g, '<span class="json-boolean">$1</span>'); // boolean/null

        jsonPreview.innerHTML = highlightedJson;

        // Add interactive collapse/expand functionality
        addJsonInteractivity();
    }

    // Add interactive elements to JSON display
    function addJsonInteractivity() {
        // Create collapse/expand buttons for arrays and objects
        const jsonLines = jsonPreview.innerHTML.split('\n');
        let indentLevel = 0;
        let processedLines = [];

        for (let i = 0; i < jsonLines.length; i++) {
            const line = jsonLines[i];
            const trimmedLine = line.trim();

            // Check for array/object start
            if (trimmedLine.endsWith('{') || trimmedLine.endsWith('[')) {
                const blockType = trimmedLine.endsWith('{') ? 'object' : 'array';
                const toggleBtn = `<span class="json-toggle" data-expanded="true">-</span>`;
                processedLines.push(line.replace(/[{\[]$/, toggleBtn + ' $&'));
                indentLevel++;
            } 
            // Check for array/object end
            else if (trimmedLine.startsWith('}') || trimmedLine.startsWith(']')) {
                indentLevel--;
                processedLines.push(line);
            }
            // Regular line
            else {
                processedLines.push(line);
            }
        }

        jsonPreview.innerHTML = processedLines.join('\n');

        // Add event listeners to toggle buttons
        document.querySelectorAll('.json-toggle').forEach(toggle => {
            toggle.addEventListener('click', function() {
                const isExpanded = this.getAttribute('data-expanded') === 'true';
                this.textContent = isExpanded ? '+' : '-';
                this.setAttribute('data-expanded', !isExpanded);

                // Find the scope of this block to collapse/expand
                let element = this.parentElement.nextElementSibling;
                let currentIndent = getIndentLevel(this.parentElement);

                while (element) {
                    const elementIndent = getIndentLevel(element);

                    // If we're back at the same indentation level or lower, we're done with this block
                    if (elementIndent <= currentIndent) {
                        break;
                    }

                    // Toggle visibility
                    element.style.display = isExpanded ? 'none' : '';
                    element = element.nextElementSibling;
                }
            });
        });

        // Helper function to get indent level of an element
        function getIndentLevel(element) {
            const text = element.textContent;
            return text.length - text.trimLeft().length;
        }
    }
});

// Add required CSS
const jsonVisualizerStyles = document.createElement('style');
jsonVisualizerStyles.textContent = `
    #json-preview {
        font-family: monospace;
        white-space: pre;
        overflow-x: auto;
        border-radius: 8px;
        padding: 15px;
        background-color: #f0f9ff;
        color: #0c4a6e;
        max-height: 500px;
        overflow-y: auto;
        box-shadow: 0 4px 15px rgba(0, 82, 204, 0.15);
        border: 1px solid rgba(0, 82, 204, 0.2);
    }

    .json-key {
        color: #0052cc;
    }

    .json-string {
        color: #0369a1;
    }

    .json-number {
        color: #0891b2;
    }

    .json-boolean {
        color: #1e40af;
    }

    .json-toggle {
        display: inline-block;
        width: 16px;
        text-align: center;
        cursor: pointer;
        color: #0052cc;
        font-weight: bold;
        user-select: none;
    }

    .json-toggle:hover {
        color: #38bdf8;
    }

    .json-visualizer h3 {
        color: #0052cc;
        margin-bottom: 1rem;
    }

    .form-check-input:checked {
        background-color: #0052cc;
        border-color: #0052cc;
    }
`;
document.head.appendChild(jsonVisualizerStyles);